import streamlit as st
from langchain_core.messages.chat import ChatMessage
from default_chain import create_course_chain
from dotenv import load_dotenv
from langchain_teddynote import logging
load_dotenv()
logging.langsmith("SOOSEMII")

#---------------------------------#
#-------- Deploy Settings --------#
#---------------------------------#
from google.oauth2 import service_account
import google.generativeai as genai  # genai import 추가

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
)

# Gemini 구성
genai.configure(
    credentials=credentials,
)


#---------------------------------#
#---------- UI Settings ----------#
#---------------------------------#
st.title("📌교과과정 도우미")

# sidebar
with st.sidebar :
    # clear dialouge
    clear_btn = st.button("♻️대화 초기화")
    catalog_btn = st.link_button("✅수강편람 다운로드", "https://board.sejong.ac.kr/boardview.do?pkid=166710&currentPage=2&searchField=ALL&siteGubun=19&menuGubun=1&bbsConfigFK=335&searchLowItem=ALL&searchValue=")
    session_id = st.text_input("세션 ID를 입력하세요.", "abc1234")
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
def add_message(role, message, avatar) :
    st.session_state["messages_course"].append(ChatMessage(role=role, content=message, avatar=avatar))

# print all dialouge
def print_messages() :
    for chat_message in st.session_state["messages_course"] :
        if chat_message.role == "user":
            avatar = "🧑‍💻"  # 사용자 아바타
        elif chat_message.role == "assistant":
            avatar = "🧽"  # AI 아바타
        else:
            avatar = None  # 다른 역할의 경우 기본 아바타 사용
        st.chat_message(chat_message.role, avatar=avatar).write(chat_message.content)


#---------------------------------#
#---------- User Action ----------#
#---------------------------------#
if "chain_course" not in st.session_state:
    with st.chat_message("assistant", avatar="🧽"):
            st.write("""
                     안녕하세요🤗 해당하는 학번에 맞는 교과과정을 알려드릴게요.\n
                     좌측 사이드바에서 학번을 입력하고 저장✅해주세요.\n
                     질문을 최대한 구체적으로 해주시면 제가 도와드리기 쉽답니다!📚
                     """)
            
if clear_btn:
    st.session_state["messages_course"] = []
if save:
    start_page, end_page = course_selection(course)
    st.session_state["chain_course"] = create_course_chain(start_page, end_page)
    with st.chat_message("assistant", avatar="🧽"):
        st.write(f"{course}학번이시군요🥰 무엇이든 물어봐주세요. 제가 도와드릴게요.")
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


# if input
if user_input :
    # temporary
    if st.session_state["chain_course"] is None:
        with st.chat_message("assistant", avatar="🧽"):
            st.write("""
                     저장 버튼을 안 누르셨나요? 눌러주셔야 제가 답을 할 수 있어요😢
                    """)

    elif st.session_state["chain_course"] is not None:
        response = st.session_state["chain_course"].stream(
            # 질문 입력
            {"question": user_input},
            config={"configurable": {"session_id": session_id}}
        )
        # user input
        st.chat_message("user", avatar="🧑‍💻").write(user_input)

        with st.chat_message("assistant", avatar="🧽"):
            # create empty container and print token by stream
            container = st.empty()
            ai_answer = ""
            for token in response :
                ai_answer += token
                container.markdown(ai_answer)

            # add dialougue to storage
            add_message("user", user_input, avatar="🧑‍💻")
            add_message("assistant", ai_answer, avatar="🧽")
    else :
        warning_msg.error("문제가 발생했습니다.")
