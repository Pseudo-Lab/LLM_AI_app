# conda activate llm_env
# streamlit run app.py
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter

from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
from newspaper import Article

from dotenv import load_dotenv
import os

# # --- 환경 설정 ---
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# # --- LangChain LLM 설정 ---
llm = ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=openai_api_key)

# # --- 프롬프트 템플릿 설정 ---
summary_prompt = PromptTemplate.from_template("""
다음 문서를 읽고, 주요 주제별로 핵심 내용을 정리해줘.
각 주제는 제목(헤드라인) 형식으로 구분하고, 그 아래에 간단한 설명을 덧붙여줘.
마치 뉴스 기사처럼 문서의 정보를 빠르게 파악할 수 있도록 해줘.

예시 형식:
# [주제1] (1~10p)
- 핵심 내용 요약

# [주제2] (11~25p)
- 핵심 내용 요약

문서:
{text}
""")

simplify_prompt = PromptTemplate.from_template("""
다음 내용을 누구나 이해할 수 있도록 쉬운 표현으로 바꿔줘. 특히 새로운 주제에 대해 흥미를 가질 수 있도록 정리해주면 좋겠어.

그리고 새롭거나 어려운 단어는 추가로 설명해줘.

내용:
{summary}
""")

# # --- 텍스트 분할 ---
def split_text_into_chunks(text, chunk_size=2000, overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " "]
    )
    return splitter.split_text(text)

# # --- PDF 텍스트 추출 ---
def extract_text(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load_and_split()
    return "\n".join([page.page_content for page in pages])

# # --- 이미지에서 텍스트 추출 ---
def extract_text_from_image(file):
    image = Image.open(file)
    return pytesseract.image_to_string(image, lang='kor+eng')

# # --- 기사 링크에서 텍스트 추출 ---
def extract_text_from_url(url):
    article = Article(url, language='ko')
    article.download()
    article.parse()
    return article.text

# # --- Streamlit UI ---
st.title("📄 멀티 입력 문서 요약기")

input_type = st.radio("문서 입력 방식 선택", ["📎 PDF", "🖼 이미지", "🔗 기사 링크"])

text = ""

if input_type == "📎 PDF":
    uploaded_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])
    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.getvalue())
        text = extract_text("temp.pdf")

elif input_type == "🖼 이미지":
    uploaded_img = st.file_uploader("이미지 업로드 (JPG, PNG)", type=["png", "jpg", "jpeg"])
    if uploaded_img:
        text = extract_text_from_image(uploaded_img)

elif input_type == "🔗 기사 링크":
    url = st.text_input("기사 링크를 입력하세요")
    if url:
        try:
            text = extract_text_from_url(url)
        except Exception as e:
            st.error(f"기사 파싱 실패: {e}")

if text:
    with st.spinner("문서 분석 중입니다..."):
        chunks = split_text_into_chunks(text)
        summaries = []
        for i, chunk in enumerate(chunks):
            try:
                prompt_filled = summary_prompt.format(text=chunk)
                partial_summary = llm([HumanMessage(content=prompt_filled)]).content
                summaries.append(partial_summary)
            except Exception as e:
                summaries.append(f"[요약 실패 {i+1}] {e}")

        final_summary = "\n\n".join(summaries)
        simplify_prompt_filled = simplify_prompt.format(summary=final_summary)
        simplified = llm([HumanMessage(content=simplify_prompt_filled)]).content

        st.subheader("📌 주제별 헤드라인 요약")
        st.markdown(final_summary)

        st.subheader("🧒 쉬운 말로 풀어서 설명")
        st.markdown(simplified)
