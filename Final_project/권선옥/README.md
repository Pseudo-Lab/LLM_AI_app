# RAG_chatbot_app

### 프로젝트명 : 부동산 전월세 실거래가 분석 및 질의응답 챗봇 서비스
- 개발 기간 : 2025-04-15 ~ 2025-05-18
- URL : https://real-estate-rag-chatbot.streamlit.app/


이 프로젝트는 전월세 실거래가 데이터를 기반으로 한 데이터 분석 및 LangChain 기반의 챗봇 서비스를 제공합니다. <br>
사용자는 Streamlit 앱을 통해 지역, 면적, 층수 등의 조건을 필터링하여 거래 데이터를 시각적으로 탐색할 수 있고, 분석 기반의 챗봇에게 해당 조건을 바탕으로 질문을 하여 인사이트를 얻을 수 있습니다.

## 주요 기능

- ✅ 전월세 실거래가 데이터 시각화
- ✅ 층수, 면적 필터링 기능
- ✅ LangGraph + LangChain을 통한 대화형 챗봇

## 사용된 기술 스택

- **Streamlit**: 웹 애플리케이션 인터페이스
- **Pandas**: 데이터 처리 및 분석
- **Matplotlib**: 시각화
- **LangChain / LangGraph**: QA 기반 챗봇
- **FAISS**: 문서 유사도 검색을 위한 벡터 스토어
- **OpenAI API**: LLM 기반 응답 생성

## 파일 구성

```
.
├── streamlit_deploy.py        # Streamlit 메인 앱
├── requirements.txt           # 의존 패키지 목록
└── README.md
```

## 설치 및 실행 방법

1. 의존성 설치

```bash
pip install -r requirements.txt
```

2. API 발급
- OpenAI API 발급
  1. [ OpenAI API 발급 페이지](https://platform.openai.com/settings/organization/api-keys) 접속
  2. `+create new secret key` 클릭 후 발급
  3. 발급된 key 복사 후 활용
  
- 공공데이터 API 발급 방법
  1. [공공데이터 - 국토교통부_연립다세대 전월세 실거래가 자료 페이지](https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15126473) 접속
  2. `활용신청` 클릭 후 신청
  3. 마이페이지 > 데이터 활용 > Open API > 활용신청 현황 > 개발계정 상세보기 > `일반 인증키(Decoding)` 복사 후 활용
     
     <img src="https://github.com/user-attachments/assets/051d8fbc-e2e8-4020-a526-af814fc0d3a1" style="width:50%;"/>



3. 환경 변수 설정 (예: `.env` 파일 또는 환경에 직접 지정)

```bash
#OpenAI API key
OPENAI_API_KEY=your_openai_api_key

#공공 데이터 API key
SERVICE_KEY=your_service_api_key

```

4. 앱 실행

```bash
streamlit run streamlit_deploy.py
```
