import os
import shutil
from pathlib import Path

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

BASE_DIR = Path(__file__).resolve().parent

FILE_PATH = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3

embedding = OllamaEmbeddings(model="bge-m3")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
)


def _load_documents():
    docs = []

    for file in FILE_PATH.rglob("*.md"):
        if file.is_file():
            print(f"loading {file.name}")

            with open(file, "r", encoding="utf-8") as f:
                doc = f.read()

            docs.append(Document(page_content=doc, metadata={"source": str(file)}))

    return docs


def _split_documents(docs):
    chunks = splitter.split_documents(docs)

    print(f"Split into {len(chunks)} chunks")

    return chunks


def build_vectorstore():
    if CHROMA_DIR.exists():
        print("Delete preexits database")

        shutil.rmtree(CHROMA_DIR)

    docs = _load_documents()
    chunks = _split_documents(docs)

    vectorstore = Chroma.from_documents(
        documents=chunks, embedding=embedding, persist_directory=str(CHROMA_DIR)
    )

    print("Vector DB created")

    return vectorstore


def main():
    build_vectorstore()


if __name__ == "__main__":
    print("Start ingest")
    main()
    print("Done")
