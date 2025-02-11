# __import__('pysqlite3')
# import sys
# import pysqlite3
# sys.modules['sqlite3'] = sys.modules["pysqlite3"]

import streamlit as st

from langchain_core.messages.chat import ChatMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI

from load_prompts import load_prompt
# from Retrievers.ensembleRetriever import ensemble_retriever
from Retrievers.contextRetriever import context_retriever

from dotenv import load_dotenv
load_dotenv()

from langsmith import Client
client = Client()



#---------------------------------#
#-------- Deploy Settings --------#
#---------------------------------#
# from google.oauth2 import service_account
# import google.generativeai as genai  # genai import 추가

# # Create API client.
# credentials = service_account.Credentials.from_service_account_info(
#     st.secrets["gcp_service_account"],
# )

# # Gemini 구성
# genai.configure(
#     credentials=credentials,
# )
###################################


#---------------------------------#
#---------- UI Settings ----------#
#---------------------------------#
st.title("🧽수세미✨")

# sidebar
with st.sidebar :
    # clear dialouge
    clear_btn = st.button("대화 초기화")
    session_id = st.text_input("세션 ID를 입력하세요.", "abc123")
    st.write("대화 기억을 위한 세션 ID입니다. 아무 값이나 넣으셔도 무방합니다.")
    st.markdown('[Powered by SMARCLE](https://www.smarcle.dev/)', unsafe_allow_html=True)

#---------------------------------#
#-------- Message Storing --------#
#---------------------------------#
# dialouge storage
if "messages_main" not in st.session_state :
    st.session_state["messages_main"] = []
    
if "store_main" not in st.session_state:
    st.session_state["store_main"] = {}

# add new message to storage
def add_message(role, message) :
    st.session_state["messages_main"].append(ChatMessage(role=role, content=message))

# print all dialouge
def print_messages() :
    for chat_message in st.session_state["messages_main"] :
        st.chat_message(chat_message.role).write(chat_message.content)

# 세션 ID를 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_ids):
    if session_ids not in st.session_state["store_main"]:  # 세션 ID가 store에 없는 경우
        # 새로운 ChatMessageHistory 객체를 생성하여 store에 저장
        st.session_state["store_main"][session_ids] = ChatMessageHistory()
    return st.session_state["store_main"][session_ids]  # 해당 세션 ID에 대한 세션 기록 반환


#---------------------------------#
#------------- Chain -------------#
#---------------------------------#
def create_chain() :
    # prompt
    prompt = load_prompt("prompts/basic.yaml")
    prompt.messages.insert(1, MessagesPlaceholder(variable_name="chat_history"))

    # model - 인증정보 추가
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        #credentials=credentials
    )

    # output parser
    output_parser = StrOutputParser()

    # chain
    chain = (
        {
            "context": lambda x: context_retriever().invoke(x["question"]),
            "question": lambda x: x["question"] if isinstance(x, dict) else x,
            "chat_history": lambda x: x["chat_history"]
        }
        | prompt
        | llm
        | output_parser
    )
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )

    return chain_with_history 

with st.chat_message("assistant"):
            st.write("""
                     안녕하세요🤗 수세미입니다🧽\n
                     수강편람에서 어떤 지점이 궁금하신가요❓ 제가 답해드릴게요‼️\n
                     최대한 구체적으로 작성해주시면 제가 더 잘 도와드릴 수 있어요💁
                     """)

#---------------------------------#
#---------- User Action ----------#
#---------------------------------#
if clear_btn:
    st.session_state["messages_main"] = []

# show previous dialouge
print_messages()

# user input
user_input = st.chat_input("궁금한 내용을 물어보세요!")

# error window
warning_msg = st.empty()

if "chain_main" not in st.session_state:
    st.session_state["chain_main"] = create_chain()

# if input
if user_input :
    # temporary
    chain = st.session_state["chain_main"]
    if chain is not None :
        response = chain.stream(
            # 질문 입력
            {"question": user_input},
            config={"configurable": {"session_id": session_id}}
        )
        # user input
        st.chat_message("user").write(user_input)

        with st.chat_message("assistant"):
            # create empty container and print token by stream
            container = st.empty()
            ai_answer = ""
            for token in response :
                ai_answer += token
                container.markdown(ai_answer)

            # add dialougue to storage
            add_message("user", user_input)
            add_message("assistant", ai_answer)
    else :
        warning_msg.error("문제가 발생했습니다.")
