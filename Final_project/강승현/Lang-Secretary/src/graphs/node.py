from mcp import ClientSession, StdioServerParameters 
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent


from src.config import WEATHER_MCP_PORT, normal_storage_config
import os    

from src.core.chain_registry import (
    supervisor_chain, 
    default_chain, 
    paper_chain, 
    weather_chain,

    paper_llm,
    weather_llm,
)




def supervisor_node(state:dict):
    user_input = state["user_input"]
    result = supervisor_chain.invoke(user_input)
    state["route"] = result.strip()
    return state


def memory_input_node(state:dict, memory):
    memory.human_message_save(state["user_input"])
    state["user_input"] = memory.get_chat_history(state["user_input"])
    return state

def memory_save_node(state:dict, memory):
    memory.ai_message_save(state["final_answer"])
    return state

def default_answer_node(state:dict):
    result = default_chain.invoke(state["user_input"])
    state["final_answer"] = result
    return state



# async def call_weather_mcp(state:dict):
#     server_params = StdioServerParameters(
#         command="python", 
#         args=[os.getcwd() + r"\src\mcp_server\weather\weather_mcp_stdio.py"]
#     )

#     # print(os.getcwd() + r"\src\mcp_server\weather\weather_mcp_stdio.py")

#     async with stdio_client(server_params) as (read, write):
#         async with ClientSession(read, write) as session:
#             await session.initialize()

#             tools = await load_mcp_tools(session)

#             agent = create_react_agent(weather_llm, tools)


#             user_input = state['user_input']
#             inputs = {"messages": [("human", user_input)]}

#             result = await agent.ainvoke(inputs)
#     state['final_answer'] = result['messages'][-1].content
#     return state


async def call_weather_mcp(state:dict):
    weather_server_info = {
            "weather": {
                "url": f"http://localhost:{WEATHER_MCP_PORT}/sse",
                "transport": "sse",
            }
        }
    client = MultiServerMCPClient(weather_server_info)
    weather_tools = await client.get_tools()
    agent = create_react_agent(weather_llm, weather_tools)

    user_input = state['user_input']
    inputs = {"messages": [("human", user_input)]}

    result = await agent.ainvoke(inputs)
    state['final_answer'] = result['messages'][-1].content
    return state



from src.core.db.search import search_arxiv_id
from src.core.db.commit import save_document, save_paper_info

from src.agents.arxiv_tools import (
    extract_arxiv_id,
    load_arxiv_document,
    extract_metadata_from_arxiv_result
)

arxiv_agent = create_react_agent(paper_llm, tools=[extract_arxiv_id])
def check_duplicated_arxiv_id(state:dict):
    try:

        
        inputs = {"messages": [("system", """
                                            extract_arxiv_id을 사용하여 
                                            사용자의 입력을 받아 올바른 형식의 arxiv_id 혹은 arxiv_url을 추출하세요.
                                            별도의 메시지를 출력하지 말고 오직 추출된 arxiv_id 혹은 arxiv_url을 반환하세요.
                                            만약 arxiv.org 도메인의 url을 입력 받았다면 arxiv_id를 추출해주세요.
                                            arxiv_id는 해당 url의 마지막 부분을 의미합니다.
                                
                                        ex) https://arxiv.org/pdf/2210.03629 다운 받아 -> 2210.03629
                                        """),
                            ("human", f'{state["user_input"].split("Human:")[-1].strip()} ~ 이 문장에서 arxiv_id를 추출해주세요.')]}
        
        arxiv_id = arxiv_agent.invoke(inputs)['messages'][-1].content

        if arxiv_id:
            duplicated_result = search_arxiv_id(arxiv_id)
            state["paper_arxiv_id"] = arxiv_id
            state["paper_duplicated_check"] = "true" if duplicated_result else "false"
            state["final_answer"] = "이미 저장된 논문입니다." if duplicated_result else "저장되지 않은 논문입니다."
            return state
        
        state["final_answer"] = "arxiv_id를 찾을 수 없습니다."
        return state
    
    except Exception as e:
        state["final_answer"] = f"오류가 발생했습니다. 다시 시도해주세요. {e}"
        state["paper_duplicated_check"] = "error"
        return state



from pathlib import Path
normal_storage_path = normal_storage_config['save_path']
def save_paper(state:dict):
    # arxiv paper 객체 로드
    paper_arxiv_obj = load_arxiv_document(state["paper_arxiv_id"]) # 최신 arxiv_id를 얻기 위해 다시 load 함.

    arxiv_id = paper_arxiv_obj.entry_id.split('/')[-1]
    state['paper_arxiv_id'] = arxiv_id


    # arxiv paper 객체를 통해 논문 다운로드
    save_path = Path(normal_storage_path) / arxiv_id
    os.makedirs(save_path, exist_ok=True)
    paper_arxiv_obj.download_pdf(dirpath=save_path, filename=f"{arxiv_id}.pdf")


    # vector db에 저장
    save_document(paper_arxiv_obj)

    # sqlite3에 저장
    metadata = extract_metadata_from_arxiv_result(paper_arxiv_obj)
    inputs = {"messages": [("system", """
                                        입력 받은 text를 한국어로 번역해줍니다.
                                        별도의 답변은 필요 없이 번역된 문장만 반환해주세요.
                                        단, 이는 논문의 abstract에 대한 내용이기 때문에 고유명사, 혹은 전문기술을 뜻하는 용어면
                                        한국어로 번역하지 말고 원문 그대로 남겨주세요.
                                      """),
                           ("human", metadata["abstract"])]}
    abstract = arxiv_agent.invoke(inputs)['messages'][-1].content
    state["paper_summary"] = abstract

    paper_info = {"arxiv_id": arxiv_id,
                  "arxiv_url": metadata["pdf_url"],
                  "title": metadata["title"],
                  "abstract": abstract,
                  "created_at": None}
    save_paper_info(paper_info)
    return state


best_result = '''
# ReAct: Synergizing Reasoning and Acting in Language Models

# Abstract
대형 language model(LLM)은 언어 이해 및 상호작용적 의사결정 과제에서 인상적인 능력을 보여주었지만, 이들의 reasoning(예: chain-of-thought prompting) 및 acting(예: action plan generation) 능력은 주로 별개의 주제로 연구되어 왔습니다.  
본 논문에서는 LLM이 reasoning trace와 과제별 action을 교차적으로 생성하도록 하여, 두 가지 간의 시너지를 극대화하는 방법을 탐구합니다.  
reasoning trace는 모델이 action plan을 유도, 추적, 갱신하고 예외를 처리하는 데 도움을 주며, action은 knowledge base나 environment와 같은 외부 소스와 상호작용하여 추가 정보를 수집할 수 있게 합니다.  
우리는 이러한 접근법을 ReAct라고 명명하고, 다양한 언어 및 의사결정 과제에 적용하여, 최첨단 baseline 대비 효과적임을 입증하였으며, reasoning이나 acting 요소가 없는 방법에 비해 인간의 해석 가능성과 신뢰성도 향상됨을 보였습니다.  
구체적으로, question answering(HotpotQA) 및 fact verification(Fever)에서 ReAct는 간단한 Wikipedia API와 상호작용함으로써 chain-of-thought reasoning에서 흔히 발생하는 hallucination 및 error propagation 문제를 극복하고, reasoning trace가 없는 baseline보다 더 해석 가능한 인간 유사 과제 해결 경로를 생성합니다.  
두 개의 interactive decision making benchmark(ALFWorld 및 WebShop)에서는, ReAct가 imitation 및 reinforcement learning 방법을 각각 34% 및 10%의 절대 성공률 차이로 능가하였으며, 단 한두 개의 in-context example만으로도 이러한 성과를 달성하였습니다.  
코드가 포함된 프로젝트 사이트: https://react-lm.github.io

# Summary
이 논문은 대형 언어 모델(LLM)의 reasoning(추론)과 acting(행동) 능력을 결합하여 시너지를 극대화하는 ReAct 프레임워크를 제안합니다.  
ReAct는 LLM이 reasoning trace(추론 과정)와 action(행동)을 교차적으로 생성하도록 하여, 두 요소가 서로를 보완하며 과제 해결 능력을 높입니다.  
추론 과정은 행동 계획을 유도하고, 행동은 외부 지식이나 환경과의 상호작용을 통해 추가 정보를 수집합니다.  
이 접근법은 question answering(HotpotQA), fact verification(Fever) 등에서 hallucination과 error propagation 문제를 줄이고, 더 해석 가능한 해결 경로를 제공합니다.  
또한, ALFWorld와 WebShop과 같은 상호작용적 의사결정 벤치마크에서 기존 imitation 및 reinforcement learning 방법보다 월등한 성능을 보였습니다.  
ReAct는 reasoning이나 acting 중 하나만 사용하는 방법에 비해 인간의 해석 가능성과 신뢰성도 크게 향상시킵니다.

# Keyword
- Large Language Model (LLM)  
- Reasoning Trace  
- Action Generation  
- Chain-of-Thought Prompting  
- ReAct Framework  
- Question Answering (HotpotQA)  
- Fact Verification (Fever)  
- Interactive Decision Making  
- ALFWorld  
- WebShop  
- Hallucination  
- Error Propagation  
- In-context Learning

# TimeLine
1. 1997년 - [Long Short-Term Memory (LSTM)](https://www.bioinf.jku.at/publications/older/2604.pdf)  
   -> RNN의 장기 의존성 문제를 해결하며 sequence modeling의 대표적 구조로 자리잡음. Transformer는 이러한 recurrence 구조를 대체함.

2. 2014년 - [Sequence to Sequence Learning with Neural Networks](https://arxiv.org/abs/1409.3215)  
   -> Encoder-Decoder 구조를 도입하여 기계번역 등 다양한 sequence transduction 문제에 적용. Transformer는 이 구조를 attention 기반으로 재해석함.

3. 2015년 - [Neural Machine Translation by Jointly Learning to Align and Translate (Bahdanau Attention)](https://arxiv.org/abs/1409.0473)  
   -> Attention mechanism을 도입하여 encoder와 decoder 간의 정보 흐름을 개선. Transformer는 이 attention을 모델의 핵심으로 확장함.

4. 2017년 - [Attention Is All You Need](https://arxiv.org/abs/1706.03762)  
   -> Recurrence와 convolution 없이 오직 attention만으로 sequence modeling을 수행하는 Transformer 아키텍처를 제안. 이후 NLP 및 다양한 분야에서 표준이 됨.

# reference
* [Chain-of-Thought Prompting Elicits Reasoning in Large Language Models (Wei et al., 2022)](https://arxiv.org/abs/2201.11903)  
  -> LLM의 chain-of-thought reasoning 기법의 핵심 논문으로, 본 논문의 reasoning trace와 직접적으로 연결됨.

* [WebGPT: Browser-assisted question-answering with human feedback (Nakano et al., 2021)](https://arxiv.org/abs/2112.09332)  
  -> LLM이 외부 환경(웹)과 상호작용하는 acting 측면의 대표적 연구로, ReAct의 action 개념과 연관.

* [HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering (Yang et al., 2018)](https://arxiv.org/abs/1809.09600)  
  -> 본 논문에서 실험에 사용된 대표적인 multi-hop QA 데이터셋. reasoning trace의 평가에 중요.

* [FEVER: a large-scale dataset for Fact Extraction and VERification (Thorne et al., 2018)](https://arxiv.org/abs/1803.05355)  
  -> fact verification task의 표준 데이터셋으로, ReAct의 성능 평가에 활용됨.

* [ALFWorld: Aligning Text and Embodied Environments for Interactive Learning (Shridhar et al., 2021)](https://arxiv.org/abs/2010.03768)  
  -> 상호작용적 의사결정 벤치마크로, ReAct의 acting 성능을 평가하는 데 사용됨.

* [WebShop: Towards Optimal Goal Fulfillment with Web-based Agents (Yao et al., 2022)](https://arxiv.org/abs/2202.01369)  
  -> 웹 기반 상호작용 환경에서의 의사결정 벤치마크로, ReAct의 실제 적용 사례.

* [Language Models are Few-Shot Learners (Brown et al., 2020)](https://arxiv.org/abs/2005.14165)  
  -> LLM의 in-context learning 능력에 대한 대표 논문으로, ReAct의 few-shot 성능과 관련.

* [Learning to summarize with human feedback (Stiennon et al., 2020)](https://arxiv.org/abs/2009.01325)  
  -> LLM의 신뢰성과 해석 가능성 향상에 관한 연구로, ReAct의 인간 유사성 평가와 연관.
'''
def summary_paper(state:dict):
    paper_summary = state["paper_summary"]
    inputs = {"messages": [("system", f"""
    human input은 논문의 abstract를 번역한 내용 입니다.
    이를 바탕으로 논문의 내용을 요약해주세요.
                            
    * 사용자에게 답변할 때에는 아래와 같은 양식을 따라주세요.
    
                            
    # [논문 title / 대괄호는 포함하지 않습니다.]
                            
    # Abstract
    [{paper_summary} / 반드시 문장 단위로 개행을 넣어주세요.]
                            
    # Summary
    [논문의 요약 / 반드시 문장 단위로 개행을 넣어주세요.]

    # Keyword
    [논문의 키워드 / 논문의 키워드는 기술명 중심으로 정리해주세요. 이 논문을 이해하기 위해서 이 키워드는 알아야한다고 판단되는 부분에 대해 작성해주세요.]

    # TimeLine
    [논문 내용에 도달하기까지의 타임라인 / 기술 발전을 중심으로 작성해주세요. / 반드시 문장 단위로 개행을 넣어주세요.]
    * 아래는 TimeLine에 대한 양식 입니다. (개수는 꼭 4개만 할 필요는 없습니다. 적거나 많아도 괜찮습니다.)
      * 1. 0000년 - [주요 기술](해당 기술 논문 url)
        -> 기술 관련 설명과 논문 주제와 어떻게 연결 되는지에 대한 내용
      * 2. 0000년 - [주요 기술](해당 기술 논문 url)
        -> 기술 관련 설명과 논문 주제와 어떻게 연결 되는지에 대한 내용
      * 3. 0000년 - [주요 기술](해당 기술 논문 url)
        -> 기술 관련 설명과 논문 주제와 어떻게 연결 되는지에 대한 내용
      * 4. 0000년 - [주요 기술](해당 기술 논문 url)
        -> 기술 관련 설명과 논문 주제와 어떻게 연결 되는지에 대한 내용
      * 5. 0000년 - [주요 기술](해당 기술 논문 url) (마지막일 경우 해당 논문 제목을 포함해주세요.)
        -> 기술 관련 설명과 논문 주제와 어떻게 연결 되는지에 대한 내용
      
    # reference
    [해당 논문을 더 깊게 이해하기 위한 추천 논문 목록 / 논문의 url까지 포함해주세요. 그리고 추천한 이유를 짧게 코맨트로 작성해주세요. / 추천 논문은 해당 paper 내 존재하는 reference 중 추천 논문이어야 합니다. / 전체 reference 중 최소 30% 이상 추천해주세요.]
    [이것은 reference에 대한 예시 입니다.
    * 해당 paper 내 존재하는 reference 중 추천 논문
      -> 추천 이유]
    

    * 사용자가 보기 편하도록 당신이 어느정도의 구조화를 해주는 것이 좋습니다.
    * markdown 파일로 저장할 것이기 때문에 당신이 적절한 마크다운 형식으로 답변해주세요.
    * 양식 외 다른 문장은 포함할 필요 없습니다.
    * 아래 내용은 가장 좋은 답변의 예시입니다. 이 답변을 참고하여 답변해주세요.
    {best_result}
                                """),
                           ("human", state["paper_summary"])]}
    answer = arxiv_agent.invoke(inputs)['messages'][-1].content
    state["final_answer"] = answer

    with open(Path(normal_storage_path) / state["paper_arxiv_id"] / f"{state['paper_arxiv_id']}.md", "w", encoding="utf-8") as f:
        f.write(answer)
    return state
