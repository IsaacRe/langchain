import os
import itertools
from typing import Any, Dict, List
from langchain import OpenAI
from langchain.chains import VectorDBQA
from langchain.callbacks import OpenAICallbackHandler
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.callbacks import get_openai_callback
from langchain.agents import AgentExecutor, load_tools, ZeroShotAgent
from langchain.experimental.autonomous_agents import BabyAGI, AutoGPT
from langchain.schema import LLMResult
from langchain.vectorstores.pgvector import PGVector
from langchain.tools.file_management import *
from langchain.tools.sandbox import SandboxTool

FILE_MANAGEMENT_TOOLS = {
    CopyFileTool,
    DeleteFileTool,
    FileSearchTool,
    MoveFileTool,
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
}


class VerboseCallbackHandler(OpenAICallbackHandler):

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        prompt_string = '\n\n'.join(prompts)
        print(f"LLM INPUT: \n{prompt_string}")
        return super().on_llm_start(serialized, prompts, **kwargs)
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        output_string = '\n\n'.join([g.text for g in itertools.chain.from_iterable(response.generations)])
        print(f"LLM OUTPUT: \n{output_string}")
        return super().on_llm_end(response, **kwargs)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
PGVECTOR_DB_URL = os.getenv("PGVECTOR_DB_URL")

openai_callback = VerboseCallbackHandler()

llm = OpenAI(
    openai_api_key=OPENAI_API_KEY,
    temperature=0,
    callbacks=[openai_callback],
)

# pinecone.init(
#     api_key=PINECONE_API_KEY,
#     environment=PINECONE_ENV,
# )

# if PINECONE_INDEX_NAME not in pinecone.list_indexes():
#     # we create a new index
#     pinecone.create_index(
#         name=PINECONE_INDEX_NAME,
#         metric='cosine',
#         dimension=1536,  # 1536 dim of text-embedding-ada-002
#     )

# pinecone_index = pinecone.Index(PINECONE_INDEX_NAME)

embed = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key=OPENAI_API_KEY,
)

# vector_store = PGVector(
#     connection_string=PGVECTOR_DB_URL,
#     embedding_function=embed,
# )

# vector_store = Pinecone(
#     index=pinecone_index,
#     embedding_function=embed,
#     text_key="text",
# )

def count_tokens(agent, query):
    with get_openai_callback() as cb:
        result = agent(query)
        print(f'Spent a total of {cb.total_tokens} tokens')

    return result

# retrieval_chain = VectorDBQA.from_chain_type(
#     vectorstore=vector_store,
#     llm=llm,
#     chain_type="stuff",  # one of "stuff", "map_reduce", "map_rerank", and "refine"
# )

tools = [SandboxTool()] #load_tools(["python_repl"])
agent = AgentExecutor.from_agent_and_tools(
    agent=ZeroShotAgent.from_llm_and_tools(
        llm=llm,
        tools=tools,
    ),
    tools=tools,
    verbose=True,
    max_iterations=3,
)

result = count_tokens(
    agent, 
    "Print 'hello'"
)
