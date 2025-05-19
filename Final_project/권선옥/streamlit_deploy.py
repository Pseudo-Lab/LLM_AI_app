import asyncio
import os
import re
import time
from datetime import datetime, timedelta
from typing import List, Optional, TypedDict

import httpx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import FuncFormatter

import pandas as pd
import requests
from io import BytesIO
import numpy as np
import streamlit as st
import xmltodict
from dotenv import load_dotenv

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents.base import Document
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage
from langchain.text_splitter import CharacterTextSplitter

from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph

# .env 파일 로드
load_dotenv(
    dotenv_path=r"/Users/sunohk/Desktop/Pseudo Lab/RAG_mini_proj/key.env"
)  

openai_key = os.getenv("OPENAI_API_KEY")
service_encoding_key = os.getenv("SERVICE_KEY")


@st.cache_data #데이터 처리 결과를 캐싱
def load_region_codes():
    # Google Drive 공유 링크의 파일 ID
    file_id = "13U8jBUf-5kuPt-hGaz6QQE3QR-VxchAI"
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    #파일 다운로드
    response = requests.get(download_url)
    response.raise_for_status()

    df = pd.read_csv(BytesIO(response.content), encoding="euc-kr", dtype={"법정동코드":str})
    df = df[df["폐지여부"]=="존재"]
    return dict(zip(df["법정동명"], df["법정동코드"]))

# 공공데이터 API 호출
async def fetch_data_httpx(service_key, lawd_cd, deal_ymd):
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent"
    params = {"serviceKey": service_key, "LAWD_CD": lawd_cd, "DEAL_YMD": deal_ymd}
    async with httpx.AsyncClient(verify=True, timeout=30.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            if not response.text.strip().startswith("<?xml"):
                return pd.DataFrame()
            data_dict = xmltodict.parse(response.content)
            items = (
                data_dict.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            )
            if isinstance(items, dict):
                items = [items]
            df = pd.DataFrame(items)
            df["deal_ymd"] = deal_ymd
            return df
        except Exception as e:
            print(f"{deal_ymd} 월 데이터 조회 실패: {str(e)}")
            return pd.DataFrame()

async def fetch_all_data(service_key, lawd_cd, months):
    tasks = [fetch_data_httpx(service_key, lawd_cd, m) for m in months]
    dfs = await asyncio.gather(*tasks)
    valid_dfs = [df for df in dfs if df is not None and not df.empty]
    if not valid_dfs:
        return pd.DataFrame()
    return pd.concat(valid_dfs, ignore_index=True)

# 데이터 전처리
def process_data(df, rent_type):
    if df.empty:
        return df
    if rent_type == "전세":
        df = df[df["monthlyRent"] == "0"]
    else:
        df = df[df["monthlyRent"] != "0"]
    df["보증금"] = df["deposit"].str.replace(",", "").str.strip().astype(float)
    df["월세"] = df["monthlyRent"].str.replace(",", "").str.strip().astype(float)
    df["년월"] = df["deal_ymd"].str[:4] + "-" + df["deal_ymd"].str[4:]
    return df


# 조회 일자 설정 함수
def get_recent_months(n=6):
    now = datetime.now()
    return [(now - timedelta(days=30 * i)).strftime("%Y%m") for i in range(n)][::-1]

# 시각화 함수
def plot_trend(df):
    plt.rcParams['font.family'] = 'Times New Roman'
    plt.rcParams['axes.unicode_minus'] = False

    monthly_mean = df.groupby("년월")[["보증금", "월세"]].mean().reset_index()
    monthly_median = df.groupby("년월")[["보증금", "월세"]].median().reset_index()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), sharex=True)
    fig.patch.set_facecolor('black')
    fig.subplots_adjust(wspace=0.3)

    # 보증금 그래프 (왼쪽)
    ax1.set_facecolor('black')
    ax1.plot(monthly_mean["년월"], monthly_mean["보증금"], marker="o", markersize=10, color="gold", label="Avg Deposit", linewidth=3, alpha=0.6)
    ax1.plot(monthly_median["년월"], monthly_median["보증금"], marker="o", markersize=10, color="orange", label="Median Deposit", linewidth=3, alpha=0.6)
    for i in range(len(monthly_mean)):
        ax1.annotate(f'{monthly_mean["보증금"].iloc[i]:,.0f}', (monthly_mean["년월"].iloc[i], monthly_mean["보증금"].iloc[i]),
                     textcoords="offset points", xytext=(0,10), ha='center', color="gold", fontsize=9, fontweight='bold')
        ax1.annotate(f'{monthly_median["보증금"].iloc[i]:,.0f}', (monthly_median["년월"].iloc[i], monthly_median["보증금"].iloc[i]),
                     textcoords="offset points", xytext=(0,-15), ha='center', color="orange", fontsize=9, fontweight='bold')
    ax1.set_title("Deposit Trend\n", color='white')
    ax1.set_xlabel("Timeline", color='white')
    ax1.set_ylabel("Amount (10,000 KRW)", color='white')
    ax1.tick_params(axis='x', rotation=90, colors='white')
    ax1.tick_params(axis='y', colors='white')
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x,_: f'{int(x):,}'))
    ax1.legend(facecolor='gray', edgecolor='white', labelcolor='white')
    ax1.grid(True, color='gray', linestyle='--', alpha=0.5)

    # 월세 그래프 (오른쪽)
    ax2.set_facecolor('black')
    ax2.plot(monthly_mean["년월"], monthly_mean["월세"], marker="s", markersize=10, color="aqua", label="Avg Rent", linewidth=3, alpha=0.6)
    ax2.plot(monthly_median["년월"], monthly_median["월세"], marker="s", markersize=10, color="skyblue", label="Median Rent", linewidth=3, alpha=0.6)
    for i in range(len(monthly_mean)):
        ax2.annotate(f'{monthly_mean["월세"].iloc[i]:,.0f}', (monthly_mean["년월"].iloc[i], monthly_mean["월세"].iloc[i]),
                     textcoords="offset points", xytext=(0,10), ha='center', color="aqua", fontsize=9, fontweight='bold')
        ax2.annotate(f'{monthly_median["월세"].iloc[i]:,.0f}', (monthly_median["년월"].iloc[i], monthly_median["월세"].iloc[i]),
                     textcoords="offset points", xytext=(0,-15), ha='center', color="skyblue", fontsize=9, fontweight='bold')
    ax2.set_title("Monthly Rent Trend\n", color='white')
    ax2.set_xlabel("Timeline", color='white')
    ax2.tick_params(axis='x', rotation=90, colors='white')
    ax2.set_ylabel("Amount (10,000 KRW)", color='white')
    ax2.tick_params(axis='y', colors='white')
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x,_: f'{int(x):,}'))
    ax2.legend(facecolor='gray', edgecolor='white', labelcolor='white')
    ax2.grid(True, color='gray', linestyle='--', alpha=0.5)

    return fig



# 상태 정의
class ChatState(
    TypedDict
):  # TypedDict : 딕셔너리의 키와 값의 타입을 미리 정의(데이터의 구조를 명확히하고 오류를 최소화)
    input: str  # 사용자의 원래 질문
    chat_history: Optional[List[BaseMessage]]
    # BaseMessage - 대화형 챗봇 메시지를 표현하기 위한 기반 클래스
    ## (참고 : https://python.langchain.com/api_reference/core/messages.html)
    # 대화 기록값에 대한 타입 힌트(값이 있을 수도 있고 없을 수도 있음)
    output: Optional[str]  # 출력 - 문자열 or None

# chatbot 생성 함수
def make_langgraph_chatbot(df):
    
    df.fillna("", inplace=True)

    # 1. 거래 정보 요약 텍스트 생성 함수
    def make_text(row):
        rent_type = "전세" if row["monthlyRent"] == "0" else "월세"
        layer_type = "반지하" if str(row.get("floor", "")) == "-1" else f'{row.get("floor", "")}층'

        return (
            f"이 거래는 {row.get('dealYear', '')}년 {row.get('dealMonth', '')}월 {row.get('dealDay', '')}일에 이루어졌다. "
            f"주소는 {row.get('umdNm', '')}({row.get('sggCd', '')} 지역코드) {row.get('jibun', '')}에 위치한 건물로, "
            f"{row.get('buildYear', '')}년에 준공된 '{row.get('mhouseNm', '')}'({row.get('houseType', '')}) 건물이다. "
            f"이 건물의 전용 면적은 {row.get('excluUseAr', '')}㎡이며, "
            f"{layer_type}층 거래가 이루어졌다. "
            f"이 거래는 {rent_type} 거래로, 보증금은 {row.get('deposit', '')}만원, 월세는 {row.get('monthlyRent', '')}만원이다. "
            f"계약 기간은 {row.get('contractTerm', '')}개월이며, 계약 구분은 {row.get('contractType', '')}이다. "
            f"갱신 요구권 사용 여부는 {row.get('useRRRight', '')}이며, 종전 계약의 보증금은 {row.get('preDeposit', '')}만원, "
            f"월세는 {row.get('preMonthlyRent', '')}만원이었다."
        )

    # 2. 벡터 DB 구성
    docs = [Document(page_content=make_text(row)) for _, row in df.iterrows()]
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    vectordb = FAISS.from_documents(chunks, OpenAIEmbeddings())

    # 3. langchain QA 정의(RAG)
    llm = ChatOpenAI(model='gpt-4o', temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
        """
        당신은 부동산 전월세 실거래 데이터 전문가입니다. 사용자의 질문에 대해 예의 바르고 정확하게 답변하세요.
        아래는 지금까지의 대화 내용입니다:
        {chat_history}
        ---
        사용자의 질문: {input}
        참고 문서:
        {context}
        """
        ),
        HumanMessagePromptTemplate.from_template("질문: {input}\n\n참고 문서:\n{context}"),
    ])


    qa_chain = create_retrieval_chain(
        vectordb.as_retriever(),  # 벡터 DB를 검색기로 변환
        create_stuff_documents_chain(
            llm, prompt
        ),  # retriever가 반환한 문서를 LLM에 입력하는 체인
        ## 참고 : https://python.langchain.com/api_reference/langchain/chains/langchain.chains.combine_documents.stuff.create_stuff_documents_chain.html
    )

    # 대화 내용 저장(langgraph의 Memory 기능)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # 노드(실제 작업을 수행하는 단위) 정의
    def user_input_node(state: ChatState):
        return {
            "input": state["input"],  # 현재 질문
            "chat_history": state.get("chat_history", []),
        }  # 이전 대화 내용 불러오기

    def get_history_as_str(messages):
        history = []
        for m in messages:
            role = "사용자" if m.type == "human" else "챗봇"
            history.append(f"{role}: {m.content}")
        return "\n".join(history)


    def response_node(state: ChatState):
        chat_history_str = get_history_as_str(memory.chat_memory.messages)
        state_with_history = dict(state)
        state_with_history["chat_history"] = chat_history_str
        result = qa_chain.invoke(state_with_history)
        memory.save_context(
            {"input": state["input"]}, {"output": result["answer"]}
        )
        return {"chat_history": memory.chat_memory.messages, "output": result["answer"]}


    # 그래프 정의(langgraph 그래프 빌더로 그래프 구성 및 컴파일)
    builder = StateGraph(ChatState)

    builder.add_node(
        "user_input", RunnableLambda(user_input_node)
    )  # RunnableLambda : 노드로 정의한 함수를 Runnable 타입(langchain에서 실행 가능한 기본 단위)으로 변환하는 wrapper
    builder.add_node("generate", RunnableLambda(response_node))

    # 그래프의 시작점 설정
    builder.set_entry_point("user_input")

    # 엣지(노드 간의 연결) 정의
    builder.add_edge("user_input", "generate")
    builder.add_edge("generate", END)

    # 그래프 컴파일(정의된 그래프를 실행 가능한 형태로 변환)
    return builder.compile()

# streamlit 실행 함수
def main():
    st.set_page_config(layout='wide')
    st.title("🏠 전월세 실거래가 분석 & 대화형 챗봇")
    
    with st.sidebar:
        st.header("API key 입력")
        openai_key = st.sidebar.text_input("OpenAI API Key", type="password")
        service_encoding_key = st.sidebar.text_input("공공 데이터 API Service Key", type="password")

        if st.button("완료"):
            if not openai_key or not service_encoding_key:
                st.warning("API Key를 모두 입력해주세요.")
            else:
                st.session_state.api_ready = True
                st.session_state.openai_key = openai_key
                st.session_state.service_key = service_encoding_key
                st.success("API Key 입력 완료!")

    if "openai_key" in st.session_state:
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_key

    st.sidebar.markdown("---")

    with st.sidebar:
        st.header("분석 옵션 선택")
        region_codes = load_region_codes()
        region = st.sidebar.selectbox("지역 선택", sorted(region_codes.keys()))
        rent_type = st.sidebar.radio("거래 유형", ["전세", "월세"])
        floor_range = st.slider("층수 범위 (지하 1층 포함)", -1, 85, (-1, 10))
        area_range = st.slider("전용 면적 범위 (㎡)", 10.0, 300.0, (30.0, 85.0))
        months_to_load = st.sidebar.slider("조회할 계약 기간(최근 n개월)", 1, 12, 6)


    st.write(f"선택 지역 : {region}")
    st.write(f"선택 유형 : {rent_type}")
    st.write(f"선택 층 범위 : {floor_range}")
    st.write(f"선택 전용 면적 범위 : {area_range}")
    st.write(f"선택 개월 수 : {months_to_load}")


    if st.button("데이터 불러오기 및 분석"):
        with st.spinner("데이터 수집 중..."):
            lawd_cd = region_codes[region][:5]
            months = get_recent_months(months_to_load)
            df_all = asyncio.run(fetch_all_data(st.session_state.service_key, lawd_cd, months))
            df_processed = process_data(df_all, rent_type)

            # 층수 및 전용 면적 필터링
            df_filtered = df_processed[
                (df_processed["floor"].astype(int) >= floor_range[0]) &
                (df_processed["floor"].astype(int) <= floor_range[1]) &
                (df_processed["excluUseAr"].astype(float) >= area_range[0]) &
                (df_processed["excluUseAr"].astype(float) <= area_range[1])
            ]

            # 데이터 처리 후 세션에 저장
            st.session_state.df_filtered = df_filtered
            st.session_state.fig = plot_trend(df_filtered)


    if "df_filtered" in st.session_state and not st.session_state.df_filtered.empty:
        df_filtered = st.session_state.df_filtered

        st.subheader(f"📈 {region} 보증금, {rent_type} 추이")
        st.pyplot(plot_trend(df_filtered))

        with st.expander("📋 시각화에 사용된 원본 데이터 보기"):
            # 계약일자 컬럼 생성
            df_filtered["계약 일자"] = (
                df_filtered["dealYear"].astype(str) + "-" +
                df_filtered["dealMonth"].astype(str).str.zfill(2) + "-" +
                df_filtered["dealDay"].astype(str).str.zfill(2)
            )

            # 컬럼명 변경 및 필요한 컬럼 선택
            df_display = df_filtered.rename(columns={
                "deposit": "보증금(만원)",
                "monthlyRent": "월세(만원)",
                "floor": "층",
                "excluUseAr": "전용 면적(㎡)",
                "buildYear": "건축 년도",
                "mhouseNm": "건물명",
                "jibun": "지번",
                "umdNm": "법정동",
                "contractTerm": "계약 기간(개월)",
                "contractType": "계약 유형",
                "useRRRight": "갱신요구권",
                "preDeposit": "이전 보증금(만원)",
                "preMonthlyRent": "이전 월세(만원)",
                "houseType": "주택 유형",
            })[["계약 일자", "지번", "법정동", "건물명", "주택 유형", "계약 기간(개월)", "계약 유형", "건축 년도", "보증금(만원)", "월세(만원)", "층", "전용 면적(㎡)"]]

            # '계약 일자' 컬럼을 datetime 형식으로 변환한 후, 'yyyy-mm-dd' 형식으로 변환
            df_display["계약 일자"] = pd.to_datetime(df_display["계약 일자"], errors='coerce')
            df_display["계약 일자"] = df_display["계약 일자"].dt.strftime("%Y-%m-%d")

            # 데이터 타입 변환 (쉼표 제거 후 변환)
            df_display["보증금(만원)"] = df_display["보증금(만원)"].replace(',', '', regex=True).astype(float)
            df_display["월세(만원)"] = df_display["월세(만원)"].replace(',', '', regex=True).astype(float)

            # 데이터 타입 변환
            df_display = df_display.astype({
                "지번": "string",
                "법정동": "string",
                "건물명": "string",
                "주택 유형": "string",
                "계약 기간(개월)": "string",
                "계약 유형": "string",
                "건축 년도": "Int64",
                "보증금(만원)": "float",
                "월세(만원)": "float",
                "층": "Int64",
                "전용 면적(㎡)": "float",
            })

            # 계약일자 기준으로 정렬
            df_display_sorted = df_display.sort_values(by="계약 일자", ascending=False).reset_index(drop=True)

            # 출력
            st.dataframe(df_display_sorted, use_container_width=True, hide_index=True)


        try:
            st.session_state.chatbot = make_langgraph_chatbot(df_filtered)
            st.success("챗봇 준비 완료! 질문해보세요.")
            st.session_state.messages = []
        except Exception as e:
            st.error(f"챗봇 생성 오류: {e}")
    else:
        st.warning("데이터가 없습니다.")

    st.markdown("---")
    st.subheader("🦜 데이터 기반 질문하기")

    if "chatbot" not in st.session_state:
        st.info("먼저 데이터를 불러와주세요.")
        return


    # 1. CSS로 사용자 메시지만 오른쪽 정렬
    st.markdown("""
    <style>
    /* 사용자 메시지(오른쪽 말풍선) */
    .st-emotion-cache-janbn0 {
        flex-direction: row-reverse !important;
        text-align: right !important;
    }
    /* 사용자 아바타도 오른쪽으로 */
    .st-emotion-cache-janbn0 .stChatAvatar {
        margin-left: 0.5rem !important;
        margin-right: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 2. 대화 기록 세션 상태 준비
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  # [(user, assistant), ...]

    # 3. 대화 내역 출력 (말풍선 형태)
    for q, a in st.session_state.chat_history:
        # 사용자 메시지: 오른쪽 말풍선
        with st.chat_message("user"):
            st.markdown(q)
        # 챗봇 메시지: 왼쪽 말풍선(기본)
        with st.chat_message("assistant"):
            st.markdown(a)

    # 4. 채팅 입력창
    if user_input := st.chat_input("질문을 입력하세요"):
        chatbot = st.session_state.get("chatbot")
        if chatbot:
            state = {"input": user_input, "chat_history": st.session_state.chat_history}
            result = chatbot.invoke(state)
            answer = result["output"]
        else:
            answer = "챗봇이 아직 준비되지 않았습니다."

        # 대화 기록에 추가
        st.session_state.chat_history.append((user_input, answer))

        # 새 메시지 즉시 출력
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            st.markdown(answer)

if __name__ == "__main__":
    main()
