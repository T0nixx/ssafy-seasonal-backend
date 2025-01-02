import os

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import UpstageDocumentParseLoader
from langchain_upstage import UpstageEmbeddings
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# upstage models
upstage_api_key = os.environ.get("UPSTAGE_API_KEY")
embedding_upstage = UpstageEmbeddings(model="embedding-query", api_key=upstage_api_key)

pinecone_api_key = os.environ.get("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
embedded_docs = os.fsencode("embedded-docs/merged")

for file in os.listdir(embedded_docs):
    filename = os.fsdecode(file)
    index_name = filename.rstrip(".pdf").split("_")[1]

    # create new index
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=4096,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    print(f"Start embedding: {index_name}")
    document_parse_loader = UpstageDocumentParseLoader(
        "embedded-docs/merged/" + filename,
        output_format="html",  # 결과물 형태 : HTML
        coordinates=False,
    )  # 이미지 OCR 좌표계 가지고 오지 않기

    docs = document_parse_loader.load()
    # Split the document into chunks

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    # Embed the splits

    splits = text_splitter.split_documents(docs)

    PineconeVectorStore.from_documents(splits, embedding_upstage, index_name=index_name)
    print(f"End embedding: {index_name}")
