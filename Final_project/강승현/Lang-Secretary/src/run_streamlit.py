import streamlit as st
import requests

from src.config import FASTAPI_PORT



backend_url = f"http://localhost:{FASTAPI_PORT}/graphbot/invoke"

st.set_page_config(page_title="Lang-Secretary", page_icon=":shark:")
st.title("Lang-Secretary")


# 세션 상태에 대화 저장
if "messages" not in st.session_state:
    st.session_state.messages = []

# 페이지 타이틀
st.title("💬")

# 기존 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력 받기
if user_prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지를 세션에 저장
    st.session_state.messages.append({"role": "user", 
                                      "content": user_prompt})
    
    # 사용자 메시지 출력
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # 여기에서 챗봇 응답 생성 (예시: 에코 응답)
    response = requests.post(f"{backend_url}", 
                                 json={
                                        "input": {
                                          "user_input": user_prompt,
                                          "route": "",
                                          "final_answer": "",

                                          "paper_arxiv_id": "",
                                          "paper_duplicated_check": "",
                                          "paper_summary": ""
                                        },
                                        "config": {},
                                        "kwargs": {}
                                      })
    
    print(response)
    print(response.json())
    
    
    try:
        # 챗봇 응답을 세션에 저장
        output = response.json()['output']['final_answer'].replace("\n", "  \n")
        st.session_state.messages.append({"role": "assistant", 
                                          "content": output})
        
        # 챗봇 응답 출력
        with st.chat_message("assistant"):
            st.markdown(output)
            # st.write(response.json()['output']['final_answer'])

    except Exception as e:
        st.session_state.messages.append({"role": "assistant", 
                                          "content": "응답에 실패하였습니다. \nException: " + str(e)})
        
        with st.chat_message("assistant"):
            st.markdown("응답에 실패하였습니다. \nException: " + str(e))
    
    
