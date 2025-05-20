from langchain_core.output_parsers import StrOutputParser

from src.core.llm import generate_llm
from src.core.prompts import SUPERVISOR_PROMPT, DEFAULT_PROMPT 


'''
supervisor_chain
'''
supervisor_llm = generate_llm(model_company="openai", model_name="gpt-4.1-nano", temperature=0.3)
supervisor_chain = SUPERVISOR_PROMPT | supervisor_llm | StrOutputParser()


'''
weather_chain
'''
weather_llm = generate_llm(model_company="openai", model_name="gpt-4.1", temperature=0.3)
weather_chain = DEFAULT_PROMPT | weather_llm | StrOutputParser()


'''
paper_chain
'''
paper_llm = generate_llm(model_company="openai", model_name="gpt-4.1", temperature=0.0)
paper_chain = DEFAULT_PROMPT | paper_llm | StrOutputParser()


'''
default_chain (fallback_chain)
'''
default_llm = generate_llm(model_company="openai", model_name="gpt-4.1", temperature=0.0)
default_chain = DEFAULT_PROMPT | default_llm | StrOutputParser()


if __name__ == "__main__":
    while True:
        user_input = input("input: ")
        print(paper_chain.invoke(user_input))
