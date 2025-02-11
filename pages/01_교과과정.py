import streamlit as st

from langchain_core.messages.chat import ChatMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI

from load_prompts import load_prompt
from major_selection import major_selection
from Retrievers.contextRetriever import course_context_retriever

from dotenv import load_dotenv
load_dotenv()


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


#---------------------------------#
#---------- UI Settings ----------#
#---------------------------------#
st.title("📌교과과정 도우미")

# sidebar
with st.sidebar :
    # clear dialouge
    clear_btn = st.button("대화 초기화")
    session_id = st.text_input("세션 ID를 입력하세요.", "abc123")
    st.write("대화 기억을 위한 세션 ID입니다. 아무 값이나 넣으셔도 무방합니다.")

    # 학번 입력
    course = st.number_input(
        "학번", step=1, max_value=25, min_value=18
    )
    # # 소속 단과대 입력
    # dept = st.selectbox(
    #     "소속 대학",
    #     ("인문과학대",
    #      "사회과학대",
    #      "경영경제대",
    #      "호텔관광대",
    #      "자연과학대",
    #      "생명과학대",
    #      "인공지능융합대",
    #      "공과대",
    #      "예체능대")
    # )
    # # 전공 입력
    # major = st.selectbox("전공", options=major_selection(dept))
    # # 학년 입력
    # level = st.selectbox("학년", options=("1", "2", "3", "4", "5", "초과학기"))
    # # 학기 입력
    # semester = st.selectbox("학기", options=("1", "2"))
    # # 편입 여부 입력
    # #bool_transfer = st.checkbox("편입")
    # 인적사항 저장
    save = st.button("인적사항 저장")
    st.markdown('[Powered by SMARCLE](https://www.smarcle.dev/)', unsafe_allow_html=True)

def course_selection(course):
    start_page, end_page = None, None
    if course==25:
        start_page, end_page = 37, 40
    if course==24:
        start_page, end_page = 41, 44
    elif course==23:
        start_page, end_page = 45, 49 
    elif course==22:
        start_page, end_page = 50, 54
    elif course==21:
        start_page, end_page = 55, 60
    elif course==20:
        start_page, end_page = 61, 66
    elif course==19:
        start_page, end_page = 67, 72
    elif course==18:
        start_page, end_page = 73, 78

    return start_page, end_page


#---------------------------------#
#-------- Message Storing --------#
#---------------------------------#
# dialouge storage
if "messages_course" not in st.session_state :
    st.session_state["messages_course"] = []
    
if "store_course" not in st.session_state:
    st.session_state["store_course"] = {}

# add new message to storage
def add_message(role, message) :
    st.session_state["messages_course"].append(ChatMessage(role=role, content=message))

# print all dialouge
def print_messages() :
    for chat_message in st.session_state["messages_course"] :
        st.chat_message(chat_message.role).write(chat_message.content)

# 세션 ID를 기반으로 세션 기록을 가져오는 함수
def get_session_history(session_ids):
    if session_ids not in st.session_state["store_course"]:  # 세션 ID가 store에 없는 경우
        # 새로운 ChatMessageHistory 객체를 생성하여 store에 저장
        st.session_state["store_course"][session_ids] = ChatMessageHistory()
    return st.session_state["store_course"][session_ids]  # 해당 세션 ID에 대한 세션 기록 반환


#---------------------------------#
#------------- Chain -------------#
#---------------------------------#
def create_chain(start_page, end_page) :
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

    # retriever
    retriever = course_context_retriever(start_page=start_page, end_page=end_page)

    # chain
    chain = (
        {
            "context": lambda x: retriever.invoke(x["question"]),
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


#---------------------------------#
#---------- User Action ----------#
#---------------------------------#
if clear_btn:
    st.session_state["messages_course"] = []
if save:
    start_page, end_page = course_selection(course)
    # # stuInfo
    # stuInfo = f"""
    #     20{course}학년도 입학자\n
    #     {dept}학 {major}\n
    #     {level}-{semester}\n
    # """

# show previous dialogue
print_messages()

# user input
user_input = st.chat_input("나는 졸업하려면 뭐 들어야돼?")

# error window
warning_msg = st.empty()

if "chain_course" not in st.session_state:
    if save:
        st.session_state["chain_course"] = create_chain(start_page, end_page)
        with st.chat_message("assistant"):
            st.write(f"""
                     {course}학번이시군요🥰 무엇이든 물어봐주세요. 제가 도와드릴게요.
                    """)
    else:
        with st.chat_message("assistant"):
            st.write("""
                     안녕하세요🤗 해당하는 학번에 맞는 교과과정을 알려드릴게요.\n
                     좌측 사이드바에서 학번을 입력하고 저장✅해주세요.\n
                     질문을 최대한 구체적으로 해주시면 제가 도와드리기 쉽답니다!📚
                     """)


# if input
if user_input :
    # temporary
    if "chain_course" not in st.session_state or not st.session_state["chain_course"]:
        with st.chat_message("assistant"):
            st.write("""
                     저장 버튼을 안 누르셨나요? 눌러주셔야 제가 답을 할 수 있어요😢
                    """)

    chain = st.session_state["chain_course"]

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
