"""Utilities for safe, structured veterinary case analysis."""

import json
import re
from typing import Any, Dict, Iterable, List

RED_FLAG_RULES = (
    ("breathing difficulty", ("difficulty breathing", "trouble breathing", "struggling to breathe", "open-mouth breathing")),
    ("collapse or unresponsiveness", ("collapsed", "collapse", "unresponsive", "not responding")),
    ("seizure", ("seizure", "seizing", "convulsion")),
    ("suspected poisoning", ("poisoned", "poisoning", "toxin", "toxic ingestion", "ate rat poison")),
    ("severe bleeding", ("severe bleeding", "profuse bleeding", "blood won't stop", "uncontrolled bleeding")),
    ("urinary obstruction", ("cannot urinate", "can't urinate", "unable to urinate", "straining to urinate with no urine")),
    ("severe abdominal emergency", ("bloated and retching", "distended abdomen", "unproductive retching")),
)

def detect_red_flags(text: str) -> List[Dict[str, str]]:
    normalized = re.sub(r"\s+", " ", (text or "").lower()).strip()
    return [{"flag": label, "evidence": phrase}
            for label, phrases in RED_FLAG_RULES
            for phrase in phrases if phrase in normalized][:]

def build_retrieval_queries(case_text: str) -> List[str]:
    """Create search queries directly from transcript text, without inventing facts."""
    text = re.sub(r"\s+", " ", (case_text or "")).strip()
    if not text:
        return []
    queries = [text]
    # Preserve symptom/disease statements from SOAP headings and transcript sentences.
    parts = re.split(r"(?<=[.!?])\s+|[\n;]+", case_text)
    for part in parts:
        query = re.sub(r"\s+", " ", part).strip(" .:-")
        if len(query.split()) >= 2 and query.lower() not in {item.lower() for item in queries}:
            queries.append(query)
    return queries[:12]


def build_evidence_context(documents: Iterable[Any]):
    blocks, sources = [], []
    for index, document in enumerate(documents or [], start=1):
        content = " ".join(str(getattr(document, "page_content", "") or "").split()).strip()
        if not content:
            continue
        metadata = getattr(document, "metadata", {}) or {}
        source = metadata.get("source") or metadata.get("title") or metadata.get("filename") or "Retrieved veterinary reference"
        ref = f"S{index}"
        blocks.append(f"[{ref}] {content}")
        sources.append({"ref": ref, "title": str(source), "page": metadata.get("page"), "snippet": content[:500]})
    return "\n\n".join(blocks), sources

def build_clinical_analysis_prompt(case_text: str, evidence: str, red_flags: List[Dict[str, str]]) -> str:
    return f'''You are a veterinary clinical decision-support assistant. Analyze the supplied transcript or SOAP note using retrieved reference passages.

The requested output is five POSSIBLE ASSOCIATED OR FUTURE CONDITIONS, not a confirmation of what the pet currently has. Treat statements such as "likely", "confirmed", or a proposed treatment plan in the case text as unverified unless supported by objective findings. For each observed symptom or condition, determine what diseases may be associated with it, develop as a complication, coexist with it, or become more likely in the future. Independently compare the clinical findings with the retrieved book passages. Rank the five possibilities from most to least relevant. Include common, important, and dangerous alternatives when clinically relevant.

Safety and evidence requirements: do not state that a diagnosis is confirmed; do not invent findings, tests, history, species, or citations; say when evidence is insufficient; do not use a retrieved passage as support unless it actually discusses that diagnosis or its relevant findings; every differential must include at least one source_refs value when relevant evidence exists; include a low-likelihood life-threatening differential when appropriate; do not provide medication doses unless explicitly supported by a cited passage.

Return ONLY valid JSON using this schema:
{{"case_summary":"string","patient_facts":{{"species":null,"breed":null,"age":null,"sex":null,"weight":null,"history":[],"symptoms":[]}},"differentials":[{{"rank":1,"condition":"string","relationship":"associated|possible_complication|future_risk|differential|unknown","likelihood":"high|medium|low|unknown","linked_findings":[],"why_it_may_occur":[],"contradicting_or_missing":[],"recommended_confirmation":[],"source_refs":["S1"]}}],"missing_information":[],"red_flags":{json.dumps(red_flags)},"urgency":"emergency|same_day|prompt|routine|unknown","disclaimer":"These are possible associated or future conditions, not confirmed diagnoses."}}}}

The differentials array MUST contain exactly five distinct possible associated, complication, future-risk, or differential conditions. Do not return fewer or more than five. If the references are insufficient for one item, use likelihood "unknown", explain that in contradicting_or_missing, and do not invent a citation.

Retrieved reference passages:
{evidence or "(No relevant reference passages were retrieved.)"}

Case transcript or SOAP note:
{case_text}'''

def parse_analysis_response(content: Any) -> Dict[str, Any]:
    if isinstance(content, dict):
        payload = content
    else:
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(content or "").strip(), flags=re.I | re.S).strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("The model did not return valid clinical-analysis JSON.")
            payload = json.loads(text[start:end + 1])
    if not isinstance(payload, dict):
        raise ValueError("Clinical-analysis response must be a JSON object.")
    payload.setdefault("differentials", [])
    payload.setdefault("missing_information", [])
    payload.setdefault("patient_facts", {})
    differentials = payload.get("differentials")
    if not isinstance(differentials, list):
        differentials = []
    payload["differentials"] = differentials[:5]
    while len(payload["differentials"]) < 5:
        rank = len(payload["differentials"]) + 1
        payload["differentials"].append({
            "rank": rank,
            "condition": "Insufficient evidence for an additional associated condition",
            "likelihood": "unknown",
            "supporting_findings": [],
            "relationship": "unknown",
            "linked_findings": [],
            "why_it_may_occur": [],
            "contradicting_or_missing": ["Additional retrieved evidence or clinical findings are needed."],
            "recommended_confirmation": [],
            "source_refs": [],
        })
    for rank, differential in enumerate(payload["differentials"], start=1):
        if isinstance(differential, dict):
            differential["rank"] = rank
    payload.setdefault("disclaimer", "These are possible associated or future conditions, not confirmed diagnoses.")
    return payload

def merge_red_flags(model_flags: Any, detected_flags: List[Dict[str, str]]):
    result = list(detected_flags)
    existing = {item.get("flag") for item in result}
    for item in model_flags if isinstance(model_flags, list) else []:
        if isinstance(item, dict) and item.get("flag") not in existing:
            result.append(item)
            existing.add(item.get("flag"))
    return result
