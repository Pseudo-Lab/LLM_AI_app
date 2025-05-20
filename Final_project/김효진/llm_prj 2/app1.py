
# import streamlit as st
# from langchain.chat_models import ChatOpenAI
# from langchain.prompts import PromptTemplate
# from langchain.document_loaders import PyPDFLoader
# from langchain.schema import HumanMessage
# from langchain.text_splitter import RecursiveCharacterTextSplitter

# from dotenv import load_dotenv
# import os

# # --- 환경 설정 ---
# load_dotenv()
# openai_api_key = os.getenv("OPENAI_API_KEY")

# # --- LangChain LLM 설정 ---
# llm = ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=openai_api_key)

# # --- 프롬프트 템플릿 설정 ---
# summary_prompt = PromptTemplate.from_template("""
# 다음 문서를 읽고, 주요 주제별로 핵심 내용을 정리해줘.
# 각 주제는 제목(헤드라인) 형식으로 구분하고, 그 아래에 간단한 설명을 덧붙여줘.
# 마치 뉴스 기사처럼 문서의 정보를 빠르게 파악할 수 있도록 해줘.

# 예시 형식:
# # [주제1] (1~10p)
# - 핵심 내용 요약

# # [주제2] (11~25p)
# - 핵심 내용 요약

# 문서:
# {text}
# """)

# simplify_prompt = PromptTemplate.from_template("""
# 다음 내용을 누구나 이해할 수 있도록 쉬운 표현으로 바꿔줘. 특히 새로운 주제에 대해 흥미를 가질 수 있도록 정리해주면 좋겠어.

# 그리고 새롭거나 어려운 단어는 추가로 설명해줘.

# 내용:
# {summary}
# """)

# # --- 텍스트 분할 ---
# def split_text_into_chunks(text, chunk_size=2000, overlap=100):
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=chunk_size,
#         chunk_overlap=overlap,
#         separators=["\n\n", "\n", ".", " "]
#     )
#     return splitter.split_text(text)

# # --- PDF 텍스트 추출 ---
# def extract_text(file_path):
#     loader = PyPDFLoader(file_path)
#     pages = loader.load_and_split()
#     return "\n".join([page.page_content for page in pages])

# # --- Streamlit UI ---
# st.title("📄 문서 요약 및 쉬운 말 변환기")

# uploaded_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])

# if uploaded_file:
#     with st.spinner("PDF 처리 중..."):
#         with open("temp.pdf", "wb") as f:
#             f.write(uploaded_file.getvalue())

#         text = extract_text("temp.pdf")
#         chunks = split_text_into_chunks(text)

#         summaries = []
#         for i, chunk in enumerate(chunks):
#             try:
#                 prompt_filled = summary_prompt.format(text=chunk)
#                 partial_summary = llm([HumanMessage(content=prompt_filled)]).content
#                 summaries.append(partial_summary)
#             except Exception as e:
#                 summaries.append(f"[요약 실패 {i+1}] {e}")

#         final_summary = "\n".join(summaries)

#         simplify_prompt_filled = simplify_prompt.format(summary=final_summary)
#         simplified = llm([HumanMessage(content=simplify_prompt_filled)]).content

#         st.subheader("📌 문서 요약")
#         st.write(final_summary)

#         st.subheader("🧒 쉬운 말로 설명")
#         st.write(simplified)

# easy_pdf_summarizer.py
import os
import requests
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import Document
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# ------------------ 환경 설정 ------------------ #
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

# ------------------ 뉴스 가져오기 ------------------ #
def fetch_news(query="한국 경제", max_articles=5):
    url = (
        f"https://gnews.io/api/v4/search?q={query}&lang=ko&country=kr&max={max_articles}&apikey={GNEWS_API_KEY}"
    )
    res = requests.get(url)
    articles = res.json().get("articles", [])
    documents = []
    for a in articles:
        content = a.get("content") or a.get("description") or ""
        metadata = {
            "title": a.get("title", ""),
            "url": a.get("url", "")
        }
        documents.append(Document(page_content=content, metadata=metadata))
    return documents

# ------------------ 벡터 저장소 구축 ------------------ #
def build_news_vectorstore():
    st.info("📡 뉴스 기사 수집 중...")
    news_docs = fetch_news()
    if not news_docs:
        st.error("뉴스 수집 실패. API 키 또는 연결 확인.")
        return None
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    news_chunks = splitter.split_documents(news_docs)
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectordb = FAISS.from_documents(news_chunks, embedding=embeddings)
    vectordb.save_local("news_vectordb")
    return vectordb

# ------------------ PDF 로딩 ------------------ #
def load_pdf(uploaded_file):
    save_path = f"tmp/{uploaded_file.name}"
    with open(save_path, "wb") as f:
        f.write(uploaded_file.read())
    loader = PyPDFLoader(save_path)
    return loader.load()

# ------------------ 쉬운 말 요약 생성 ------------------ #
def summarize_easy(pdf_docs, retriever):
    pdf_text = " ".join([doc.page_content for doc in pdf_docs])
    system_prompt = """
    너는 초등학교 선생님이야. 아래 내용과 관련된 최신 뉴스 기사도 함께 참고해서,
    이 PDF 내용을 초등학생도 이해할 수 있도록 아주 쉽게, 핵심만 요약해줘.
    
    요약은 아래와 같은 구조를 따라줘:
    
    1. 문서 전체의 개요를 먼저 설명해줘 (무엇에 관한 문서인지, 어떻게 구성되어 있는지)
    2. 주요 내용을 쉽게 정리해줘
    3. 새롭게 알게 된 정보 중에서 흥미로운 점을 알려줘

    형식은 아래처럼 써줘:
    📘 문서 개요:
    ...

    🧠 핵심 내용:
    ...

    💡 흥미로운 점:
    """

    llm = ChatOpenAI(
        temperature=0.2, model="gpt-4o", openai_api_key=OPENAI_API_KEY
    )
    
    prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template=system_prompt + "\n\nPDF 내용: {context}\n\n질문: {question}"
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={
            "prompt": (
                prompt_template
            ),
        },
        return_source_documents=True,
    )
    
    output = qa_chain.invoke({"query": "이 문서를 관심없던 사람도 흥미를 가질 수 있게 요약해줘."})
    
    return output

# ------------------ Streamlit 앱 ------------------ #
st.set_page_config(page_title="PDF 쉬운 요약기", layout="centered")
st.title("📝 뉴스 참조 PDF 쉬운 요약기")

uploaded_file = st.file_uploader("📄 PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file:
    st.success("✅ PDF 업로드 완료")

    if not os.path.exists("news_vectordb"):
        st.warning("🧠 뉴스 벡터 저장소가 없어, 지금 생성할게요...")
        build_news_vectorstore()

    # PDF 처리
    pdf_docs = load_pdf(uploaded_file)

    # 벡터 불러오기
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vectordb = FAISS.load_local(
        "news_vectordb", embeddings, allow_dangerous_deserialization=True
    )
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})

    if st.button("🪄 쉬운 요약 생성하기"):
        with st.spinner("요약 중..."):
            result = summarize_easy(pdf_docs, retriever)
            summary = result["result"]
            sources = result["source_documents"]
        st.subheader("📘 쉬운 요약 결과")
        st.write(summary)
        
        # 참조 뉴스 기사
        st.subheader("📰 요약에 참조된 뉴스 기사")
        for i, doc in enumerate(sources, 1):
            title = doc.metadata.get("title", f"기사 {i}")
            url = doc.metadata.get("url", None)

            if url:
                st.markdown(f"[{title}]({url})")
            else:
                st.markdown(f"🔗 {title} (링크 없음)")
else:
    st.info("왼쪽에서 PDF 파일을 업로드해주세요.")