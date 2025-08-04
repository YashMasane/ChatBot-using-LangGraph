import streamlit as st
from langchain_core.messages import HumanMessage
from backend import workflow

CONFIG = {'configurable': {'thread_id': '1'}}

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

for messages in st.session_state['chat_history']:
    with st.chat_message(messages['role']):
        st.text(messages['content'])

user_input = st.chat_input('Type here')

if user_input:
    st.session_state['chat_history'].append({'role': 'user', 'content':user_input})
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
    
    st.session_state['chat_history'].append({'role': 'assistant', 'content': ai_mesasge})
