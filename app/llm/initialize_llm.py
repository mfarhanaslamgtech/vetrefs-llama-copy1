import os
from dotenv import load_dotenv, find_dotenv
# from langchain_community.chat_models import ChatOllama
load_dotenv(find_dotenv())

from langchain_community.llms import Ollama
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager


# def initialize_llm():
#     """
#     Determine the appropriate OpenAI model based on the date and initialize ChatOpenAI object.
#     """
#     llm_name = os.environ.get('LLM_NAME')
#     llm = ChatOllama(model=llm_name)
#     return llm

def initialize_llm():

    llm = Ollama(base_url="http://localhost:11434",
                                    model="llama3:8b",
                                    verbose=True,
                                    callback_manager=CallbackManager(
                                        [StreamingStdOutCallbackHandler()]),
                                    )
    return llm 