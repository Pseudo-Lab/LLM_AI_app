from langchain_community.document_loaders import ArxivLoader
from langchain.tools import tool

import arxiv
import re



@tool
def extract_arxiv_id(user_input:str) -> str:
    """
    user_input으로부터 arxiv_id 혹은 arxiv_url을 추출하는 tool 입니다.

    user_input: 사용자의 입력
    return: arxiv_id 혹은 arxiv_url

    arxiv_id는 다음과 같은 형식을 가집니다.
    2210.03629
    2210.03629v1

    arxiv_url은 다음과 같은 형식을 가집니다.
    https://arxiv.org/pdf/2210.03629
    https://arxiv.org/abs/2210.03629
    """
    # ex) "https://arxiv.org/pdf/2210.03629" / "https://arxiv.org/abs/2210.03629"
    user_input = user_input.replace("abs", "pdf")
    match = re.search(r'arxiv\.org/pdf/(\d{4}\.\d{5})(v\d+)?', user_input)
    if match:
        return f"{match.group(1)}"
    
    # "2210.03629v1"
    if isinstance(user_input, str):
        if re.match(r'\d{4}\.\d{5}(v\d+)?', str(user_input)):
            return f"{user_input}"
    
    return False



def load_arxiv_document(arxiv_id: str) -> arxiv.Result:
    '''
    arxiv_id: arxiv id

    arxiv 라이브러리를 통해 논문을 다운받아 arxiv.Result 객체 반환
    '''
    try:
        search_by_id = arxiv.Search(id_list=[arxiv_id])
        paper = next(arxiv.Client().results(search_by_id))
        return paper
    
    except Exception as e:
        return None



def extract_metadata_from_arxiv_result(paper: arxiv.Result):
    '''
    paper: arxiv.Result 객체

    arxiv.Result 객체를 Document 형식으로 반환
    '''
    if paper is None:
        return "논문을 Document 객체로 변환하는 과정에서 오류가 발생했습니다."
    
    metadata = {
                    "title": paper.title,
                    "authors": ', '.join([author.name for author in paper.authors]),
                    "abstract": paper.summary,
                    "pdf_url": paper.pdf_url,
                    "entry_id": paper.entry_id,
                    "arxiv_id": paper.entry_id.split("/")[-1],
                }

    return metadata
