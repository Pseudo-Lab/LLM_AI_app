from langchain_openai import ChatOpenAI

from src.config import OPENAI_API_KEY




'''
TODO
claude
gemini
groq

모델 추가
'''
def generate_llm(model_company:str="openai", model_name:str="gpt-4.1", temperature:float=0.3, KEY:str=OPENAI_API_KEY):
    '''
    model_company: 사용할 모델의 회사
    model_name: 사용할 모델의 이름
    temperature: 모델의 온도
    '''
    if model_company == "openai":
        return ChatOpenAI(model=model_name, temperature=temperature, openai_api_key=KEY)
    else:
        raise ValueError(f"Invalid model company: {model_company}")
