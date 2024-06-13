from langchain_community.vectorstores import Chroma
# # from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
# OllamaEmbeddings(model="nomic-embed-text",show_progress=True)


def initialize_embeddings():
    """
    Initialize OpenAI embeddings, vector database, and language model (llm).
    """
    embeddings = OllamaEmbeddings(model="nomic-embed-text", show_progress=True)
    # embeddings = HuggingFaceEmbeddings()
    vectordb = Chroma(
        persist_directory=r"D:\private_llm\app\embeddings\vectordb",
        embedding_function=embeddings
    )
    # return vectordb 
    return vectordb


