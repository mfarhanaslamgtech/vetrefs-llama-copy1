# Utility functions for the chatbot module
import json
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    messages_from_dict,
    messages_to_dict)



    #func for making messages serialized before storing in db.
def serialize_memory_messages(chain_name):
    """
Serialize messages extracted from the memory of a chat chain.

Args:
    chain_name (ChatChain): The chat chain from which messages are extracted.

Returns:
    str: A JSON string representing the serialized messages.
"""
    extracted_messages = chain_name.memory.chat_memory.messages
    ingest_to_db=messages_to_dict(extracted_messages)
    serialized_messages = json.dumps(ingest_to_db)
    return serialized_messages

#func for deserializing messages
def deserialized_db_messages(messages):
    """_summary_

    Args:
        messages (_type_): _description_

    Returns:
        _type_: _description_
    """
    retrieved_messages = messages_from_dict(json.loads(messages["messages"]))
    retrieved_messages = retrieved_messages[-5:]
    return retrieved_messages