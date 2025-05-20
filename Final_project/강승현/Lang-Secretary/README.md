# 0. 프로젝트 개요
해당 프로젝트는 모 중소기업에 ai agent 개발자 직무에 면접을 보러갔다가   
자신의 능력에 대해 부족함을 깨닫고 제대로 된 개발을 해보자는 취지해서 시작함.  

면접에서 느낀 나의 부족함은 크게 세가지  
첫번째, `프로젝트 설계`에 대한 지식 부족  
두번째, 구현에만 신경 쓰며 이걸 왜 만드는지에 대한 `문제 정의 및 해결`에는 등한시  
세번째, 만들고자 하는 앱(혹은 모델)에 대해서 `정확한 목표 스펙` 미설정  

나의 개발 실력이 부족한 만큼.  
해당 프로젝트로 성장하려는 것이 목표이며 동시에   
나의 성장을 도와줄 훌륭한 agent를 만드는게 목표이며  
동시에 나와 같이 비전공으로 시작하여 개발자의 꿈을 꾸는 사람들에게  
도움이 되기를 바라는 마음에 해당 프로젝트를 시작함.



___
## 실행 환경
```
window 10
python 3.11.5
```

## 실행 방법

### 1. python package 설치
```
python -m pip install -r requierments.txt
```

### 2. .env 설정
```
.env.example 참조
```

### 2. api server 실행
```
python -m src.run_api
```

### 3. frontend server 실행  
```
python -m streamlit run ./src/run_streamlit.py
```
___


## 구현 상황
|agent name|state|
|----------|-----|
|Weather agnet|✅|
|Paper agnet|👨‍💻|
|Study agnet|❌|


<br><br><br>






# 1. 문제 정의
    a. 개발자로 일하기엔 실력이 부족하다. 어떻게 하면 ai를 활용하여 빠른 시간 내에 지식을 습득할 수 있을까?

<br><br><br>

# 2. 요구사항 정리
    a. 아침마다 아침 날씨와 해당 날씨에 맞는 복장을 브리핑 <개인적으로 많이 사용해서 넣음.>
    b. arxiv 링크를 주면 해당 논문을 download하여 vectorDB에 저장
    c. 해당 논문을 사용자가 이해할 수 있도록 리뷰
        1) 영어 -> 한국어 번역
        2) Abstract 번역
        3) 주요 개념과 키 포인트
    d. 추후 공부할 내용에 대한 키워드를 저장해두었다가 나중에 알려주기
    e. 공부 할 내용에 대해 기반 지식부터 설명
    f. 대화 내용은 일자 기준으로 저장하며 언제든지 불러올 수 있음


<br><br><br>

# 3. 아키텍처 설계

## 3.1 시스템 구성도


## 3.2 주요 컴포넌트
1. Categorize LLM
   - 가장 먼저 사용자 입력을 받는 LLM
   - 사용자 요청을 분류하여 알맞은 LLM에 전달함.

2. Study LLM
   - ...

3. Weather Agent
   - 당일 날씨를 알려줌. (위치는 입력 받거나 `.env`파일 내 Default 값을 따름)
   - 날씨에 따른 추천 복장도 함께 알려줌. (미구현)

4. Paper Agent
   - ...

5. Paper Agent
   - ...

## 3.3 데이터 흐름
1. 사용자 입력 → Categorize LLM
2. Categorize LLM → (Study LLM / Weather LLM / Paper LLM / Default LLM)
3. LLM   
    3-a. Study LLM -> ...    
    3-b. Weather LLM    
    3-c. Paper LLM -> ...    
    3-d. Default LLM -> gpt-4o 기본 응답
4. 처리 결과 → 사용자 응답

## 3.4 기술 스택
- Backend: FastAPI
- Frontend: streamlit
- LLM: OpenAI GPT 
- LLM Framework: LangChain, LangGraph
- Vector DB: Chroma
- Storage: SQLite (대화 기록)


<br><br><br>


# 4. 세부 설계

<br><br><br>


# 5. 추후 개발 사항
- 미완성 agent 완성
- backend/frontend 예외처리 추가
- logging
- TEST + CI/CD (git actions + AWS light sail)
- agent 내 api 사용 관련 함수들 비동기 전환
- 문서화 및 다이어그램 작성



<br><br><br>


# 6. ETC

* Docker-compose로 배포를 하고싶으나 frontend 부분의 크기가 워낙 작아서 오히려 비효율이라 판단합니다.  
그렇기에 차라리 docker image를 하나로만 생성하고 `run.sh`을 통해 api-server와 frontend server를 실행하는게 더 효율적이라 판단합니다.
* 단, Docker-compose에 대한 yml은 남겨두도록 하겠습니다.
