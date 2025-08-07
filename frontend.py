import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from backend import workflow
import uuid

# ***************************** utility functions *************************************************


def generate_threadid():
    thread_id = uuid.uuid4()
    return thread_id


def add_chat_thread(thread_id):
    if thread_id not in st.session_state['chat_thread']:
        st.session_state['chat_thread'].append(thread_id)


def reset_chat():
    thread_id = generate_threadid()
    st.session_state['thread_id'] = thread_id
    add_chat_thread(st.session_state['thread_id'])
    st.session_state['chat_history'] = []


def load_messages(thread_id):
    return workflow.get_state(config={'configurable': {'thread_id': thread_id}}).values['messages']


def generate_chat_name(input_str, name_list):
    llm = ChatOpenAI()
    template = (
        "You are a helpful assistant. Generate a name based on the following user input:\n"
        "{user_input}\n\n"
        "The name must be a maximum of five words.\n"
        "Make sure the name is different from the following list:\n{existing_names}"
    )

    prompt_template = PromptTemplate.from_template(template)
    if isinstance(name_list, list):
        name_list_str = ", ".join(name_list)
    else:
        name_list_str = str(name_list)
    prompt = prompt_template.format(
        user_input=input_str, existing_names=name_list_str)
    name = llm.invoke(prompt)
    return name.content


# ********************************* Session State ************************************


if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_threadid()

if 'chat_thread' not in st.session_state:
    st.session_state['chat_thread'] = []

add_chat_thread(st.session_state['thread_id'])

if 'chat_names' not in st.session_state:
    st.session_state['chat_names'] = {}


# ********************************** main UI ***********************************

st.sidebar.title('LangGraph ChatBot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('Your Chats')

for thread_id in st.session_state['chat_thread'][::-1]:

    chat_name = st.session_state['chat_names'].get(thread_id, str(thread_id)) 

    if st.sidebar.button(chat_name, key=str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_messages(st.session_state['thread_id'])

        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'

            temp_messages.append({'role': role, 'content': msg.content})
        st.session_state['chat_history'] = temp_messages

CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

for messages_history in st.session_state['chat_history']:
    with st.chat_message(messages_history['role']):
        st.text(messages_history['content'])

user_input = st.chat_input('Type here')

if user_input:

    if len(st.session_state['chat_history']) == 0:
        chat_name = generate_chat_name(user_input, list(
            st.session_state['chat_names'].values()))
        st.session_state['chat_names'][st.session_state['thread_id']] = chat_name

    st.session_state['chat_history'].append(
        {'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    # response = workflow.invoke({'messages': HumanMessage(user_input)}, config=CONFIG)
    # ai_response = response['messages'][-1].content
    # st.session_state['chat_history'].append({'role': 'assistant', 'content': ai_response})
    with st.chat_message('assistant'):
        ai_mesasge = st.write_stream(
            message.content for message, metadata in workflow.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    st.session_state['chat_history'].append(
        {'role': 'assistant', 'content': ai_mesasge})
