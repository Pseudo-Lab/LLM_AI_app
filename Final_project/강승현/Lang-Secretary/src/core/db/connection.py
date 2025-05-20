from pathlib import Path

import os
import sqlite3
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from src.config import chroma_config, sqlite3_config

VECTOR_DB_PATH = chroma_config["save_path"]
SQLITE3_DB_PATH = sqlite3_config["save_path"]


def vector_db_connection(persist_directory:str = VECTOR_DB_PATH) -> Chroma:
    '''
    Local Vector DB에 연결합니다.
    '''
    if Path(persist_directory).exists():
        print("Load Vector DB from ", persist_directory)
    else:
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        print("Init Vector DB")

    return Chroma(
        embedding_function=OpenAIEmbeddings(),
        persist_directory=persist_directory
    )


def sqlite3_db_connection(db_path:str = SQLITE3_DB_PATH) -> sqlite3.Connection:
    '''
    Local SQLite3 DB에 연결합니다.
    '''
    if Path(db_path).exists():
        print("Load SQLite3 DB from ", db_path)
        conn = sqlite3.connect(db_path)
        return conn
    else:
        os.makedirs(Path(db_path).parent, exist_ok=True)
        print("Init SQLite3 DB")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        default_query = '''
            CREATE TABLE IF NOT EXISTS papers (
                arxiv_id TEXT PRIMARY KEY,
                arxiv_url TEXT,
                title TEXT,
                abstract TEXT,
                created_at TEXT
            )
        '''
        cursor.execute(default_query)
        conn.commit()
        return conn



if __name__ == "__main__":
    vector_db = vector_db_connection()
    print(vector_db)
