from src.core.db.connection import vector_db_connection, sqlite3_db_connection
from src.config import chroma_config


TOP_K = chroma_config["search"]["top_k"]
MRR_THRESHOLD = chroma_config["search"]["mmr_threshold"]


def search_vector_db(query:str):
    _vector_db = vector_db_connection()
    _results = _vector_db.similarity_search_with_relevance_scores(query, 
                                                                  k=TOP_K)
    
    _filtered_results = [doc for doc, score in _results if score >= MRR_THRESHOLD]
    return _filtered_results
    
    
from langchain.chains import create_history_aware_retriever
def search_vector_db_with_retrieval(query:str, llm, memory):
    _vector_db = vector_db_connection()
    _retriever = _vector_db.as_retriever(
                                            search_type="similarity_score_threshold",
                                            search_kwargs={'score_threshold': 0.8},
                                            k=5
                                        )
    
    _response = create_history_aware_retriever(llm=llm,
                                               retriever=_retriever,
                                               ).invoke({'query': query,
                                                         'chat_history': memory})
    return _response

def search_arxiv_id(arxiv_id:str):
    '''
    Local SQLite3 DB에서 papers 테이블 내 arxiv_id 컬럼의 모든 값을 조회합니다.
    이는 arxiv_id 값이 존재하는지 확인하기 위함 입니다.
    '''
    conn = sqlite3_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT arxiv_id FROM papers;")
    rows = cursor.fetchall()
    arxiv_ids = [row[0] for row in rows]
    return True if arxiv_id in arxiv_ids else False





