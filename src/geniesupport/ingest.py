import os, glob
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from src.geniesupport.config import EMBED_MODEL, PERSIST_DIR

DOCS_DIR = "data/help_docs"

def load_docs():
    docs = []
    for path in glob.glob(os.path.join(DOCS_DIR, "*.md")):
        title = os.path.splitext(os.path.basename(path))[0].replace("_", " ").title()
        with open(path, encoding="utf-8") as f:
            docs.append(Document(page_content=f.read(), metadata={"title": title}))
    print(f"Loaded {len(docs)} help docs.")
    return docs

def main():
    os.makedirs(PERSIST_DIR, exist_ok=True)
    docs = load_docs()
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=700, chunk_overlap=100
    ).split_documents(docs)
    print(f"Split into {len(chunks)} chunks.")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    Chroma.from_documents(chunks, embeddings, persist_directory=PERSIST_DIR)
    print(f"Vector store saved to {PERSIST_DIR}.")

if __name__ == "__main__":
    main()