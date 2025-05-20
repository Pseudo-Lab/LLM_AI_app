from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


from src.core.db.connection import vector_db_connection, sqlite3_db_connection
from datetime import datetime

import yaml

from src.config import chroma_config 

CHUNK_SIZE = chroma_config["load"]["chunk_size"]
CHUNK_OVERLAP = chroma_config["load"]["overlap_size"]


def save_document(document):
    '''
    Local Vector DB에 langchain_core.documents.Document 타입의 문서를 저장합니다.
    '''
    vector_db = vector_db_connection()

    if isinstance(document, Document):
        pass

    elif isinstance(document, str):
        vector_db = vector_db_connection()
        loader = PyPDFLoader(document)
        document = loader.load()

    else:
        return "Document 저장에 실패하였습니다. 오류 메세지: 지원하지 않는 타입입니다."

    
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, 
                                                chunk_overlap=CHUNK_OVERLAP)
        split_docs = splitter.split_documents([document])

        vector_db.add_documents(split_docs)
        del vector_db
        return "Document 저장에 성공하였습니다."
            
    except Exception as e:
        return f"Document 저장에 실패하였습니다. 오류 메세지지: {e}"
    


def save_paper_info(paper_info:dict):
    '''
    Local SQLite3 DB에 논문 정보를 저장합니다.
    '''
    try:
        paper_info['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO papers (arxiv_id, arxiv_url, title, abstract, created_at) VALUES (?, ?, ?, ?, ?)", (paper_info['arxiv_id'], paper_info['arxiv_url'], paper_info['title'], paper_info['abstract'], paper_info['created_at']))
        conn.commit()
        conn.close()
        return "논문 정보 저장에 성공하였습니다."
    
    except Exception as e:
        return f"논문 정보 저장에 실패하였습니다. 오류 메세지: {e}"




