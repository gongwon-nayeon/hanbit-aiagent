from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    DOCUMENTS_DIR = "./supervisor_agent_triple/documents" # [ 1 ]
    DB_PATH = "./supervisor_agent_triple/chroma_db"

    document_paths = []
    if os.path.exists(DOCUMENTS_DIR):
        for file_name in os.listdir(DOCUMENTS_DIR):
            file_path = os.path.join(DOCUMENTS_DIR, file_name)
            if os.path.isfile(file_path):
                document_paths.append(file_path)

    all_docs = []

    for file_path in document_paths: # [ 2]
        if os.path.exists(file_path):
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension == '.pdf':
                loader = PyPDFLoader(file_path)
                pages = []
                for page in loader.lazy_load():
                    pages.append(page)

            elif file_extension in ['.docx', '.doc']:
                loader = Docx2txtLoader(file_path)
                pages = loader.load()

            text_splitter = RecursiveCharacterTextSplitter( # [ 3 ]
                chunk_size=1000,
                chunk_overlap=200
            )
            docs = text_splitter.split_documents(pages)

            file_name = os.path.basename(file_path)
            file_name_without_ext = os.path.splitext(file_name)[0]

            for doc in docs: # [ 4 ]
                original_content = doc.page_content
                doc.page_content = f"[문서명: {file_name}]\n\n{original_content}"

                doc.metadata.update({
                    'file_name': file_name,
                    'file_name_without_ext': file_name_without_ext,
                    'file_extension': file_extension,
                    'file_type': 'pdf' if file_extension == '.pdf' else 'word'
                })

            all_docs.extend(docs)

    vectorstore = Chroma.from_documents( # [ 5 ]
        documents=all_docs,
        embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
        persist_directory=DB_PATH,
        collection_name="documents"
    )

if __name__ == "__main__":
    main()
