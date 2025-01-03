import os, json, asyncio
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.chains import RetrievalQA
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import ChatUpstage
from langchain_upstage import UpstageEmbeddings
from pinecone import Pinecone, ServerlessSpec
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

with open("dictionary.json", encoding="utf-8") as f:
    stock_dict = json.load(f)

embedded_docs = os.fsencode("embedded-docs/merged")

# upstage models
chat_upstage = ChatUpstage()
upstage_api_key = os.environ.get("UPSTAGE_API_KEY")
embedding_upstage = UpstageEmbeddings(model="embedding-query", api_key=upstage_api_key)

pinecone_api_key = os.environ.get("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
index_name = ""

# load vector store
pinecone_vectorstore = []

for i in range(5):
    # create new index
    index_name = f"00{i}"
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=4096,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    pinecone_vectorstore.append(
        PineconeVectorStore(index=pc.Index(index_name), embedding=embedding_upstage)
    )

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class AssistantRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]  # Entire conversation for naive mode


class MessageRequest(BaseModel):
    message: str


async def retrieve_information(i, message, ref_list):
    pinecone_retriever = pinecone_vectorstore[i].as_retriever(
        search_type="mmr",  # default : similarity(유사도) / mmr 알고리즘
        search_kwargs={"k": 3},  # 쿼리와 관련된 chunk를 3개 검색하기 (default : 4)
    )
    qa = RetrievalQA.from_chain_type(
        llm=chat_upstage,
        chain_type="stuff",
        retriever=pinecone_retriever,
        return_source_documents=True,
    )
    ref_list[i] = qa(
        f"To a given question, search the embedded vector and retrieve relevant companys' information in few sentences, split by new lines.\n(If the given information is not enough, just return the empty string.\nquestion: {message}"
    )["result"]


@app.post("/chat")
async def chat_endpoint(req: MessageRequest):
    info_list = [""] * 5
    await asyncio.wait(
        [
            asyncio.create_task(retrieve_information(i, req.message, info_list))
            for i in range(5)
        ]
    )
    information_acquired = "\n".join(info_list)

    result = chat_upstage.invoke(
        f"Considering following information, answer the question in Korean.\ninformation: {information_acquired}\nquestion: {req.message}"
    )
    return {"reply": result}


# @app.post("/assistant")
# async def assistant_endpoint(req: AssistantRequest):
#     assistant = await openai.beta.assistants.retrieve("asst_tc4AhtsAjNJnRtpJmy1gjJOE")
#
#     if req.thread_id:
#         # We have an existing thread, append user message
#         await openai.beta.threads.messages.create(
#             thread_id=req.thread_id, role="user", content=req.message
#         )
#         thread_id = req.thread_id
#     else:
#         # Create a new thread with user message
#         thread = await openai.beta.threads.create(
#             messages=[{"role": "user", "content": req.message}]
#         )
#         thread_id = thread.id
#
#     # Run and wait until complete
#     await openai.beta.threads.runs.create_and_poll(
#         thread_id=thread_id, assistant_id=assistant.id
#     )
#
#     # Now retrieve messages for this thread
#     # messages.list returns an async iterator, so let's gather them into a list
#     all_messages = [
#         m async for m in openai.beta.threads.messages.list(thread_id=thread_id)
#     ]
#     print(all_messages)
#
#     # The assistant's reply should be the last message with role=assistant
#     assistant_reply = all_messages[0].content[0].text.value
#
#     return {"reply": assistant_reply, "thread_id": thread_id}


@app.get("/health")
@app.get("/")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
