from langchain.prompts import ChatPromptTemplate


supervisor_system_message = '''
    다음 문장이 어떤 유형에 더 유사한지 골라주세요.

    답변은 반드시 단어로만 해주세요. [weather, paper, default]

    ex)
    Question: 오늘 강남구 날씨 알려줘
    Answer: weather

    Question: https://arxiv.org/abs/2210.03629 다운 받아서 vector db에 저장해
    Answer: paper

    Question: shutil 라이브러리에서 copy, copy2, copyfile 각각 차이점 알려줘
    Answer: default
    

    선택에 대한 힌트를 줄게
    arxiv.org/ 이와 같은 url을 입력 받았다면 이는 paper으로 분류하면 돼
    '''


SUPERVISOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", supervisor_system_message.strip()),
    ("human", "{input}")
])



default_system_message = '''
    1. <CHAT_HISTORY_START>와 <CHAT_HISTORY_END> 사이에 있는 대화들은 전부 너와 내가 함께 나눈 대화니까. 기억해두고 앞으로 대화할 때 참고해서 답변해줘
    2. <CHAT_HISTORY_START>와 <CHAT_HISTORY_END>는 INPUT 가장 처음에만 등장하니 이후에 등장하는 CHAT_HISTORY는 무시해
    '''


DEFAULT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", default_system_message.strip()),
    ("human", "{input}")
])