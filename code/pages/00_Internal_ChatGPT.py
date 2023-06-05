'''Internal ChatGPT page of the Streamlit app.'''
import os
import streamlit as st
from streamlit_chat import message
from utilities.helper import LLMHelper
from utilities.authenticate import set_st_auth_vars
from utilities.pagehandler import delete_page, all_pages

def clear_text_input():
    'Function to clear text input'
    st.session_state['question'] = st.session_state['input']
    st.session_state['input'] = ""

def clear_chat_data():
    'Function to clear chat data'
    st.session_state['input'] = ""
    st.session_state['chat_history'] = []
    st.session_state['source_documents'] = []


set_st_auth_vars()

if os.getenv('AAD_General_SG') in st.session_state["user_groups"] or \
    os.getenv('AAD_Admin_SG') in st.session_state["user_groups"]:
    # Initialize chat history
    if 'question' not in st.session_state:
        st.session_state['question'] = None
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'source_documents' not in st.session_state:
        st.session_state['source_documents'] = []

    llm_helper = LLMHelper()

    # Chat
    st.text_input("You: ",
                  placeholder="type your question",
                  key="input", on_change=clear_text_input)
    clear_chat = st.button("Clear chat", key="clear_chat", on_click=clear_chat_data)

    if st.session_state['question']:
        question, result, _, sources = llm_helper.get_semantic_answer_lang_chain(
            st.session_state['question'], st.session_state['chat_history'])
        st.session_state['chat_history'].append((question, result))
        st.session_state['source_documents'].append(sources)

    if st.session_state['chat_history']:
        for i in range(len(st.session_state['chat_history'])-1, -1, -1):
            message(st.session_state['chat_history'][i][1], key=str(i))
            st.markdown(f'\n\nSources: {st.session_state["source_documents"][i]}')
            message(st.session_state['chat_history'][i][0], is_user=True, key=str(i) + '_user')
elif not st.session_state["authenticated"]:
    st.write("You are not authorized to view this page.")
else:
    for page in all_pages:
        delete_page(__file__, page)
    st.write("You are not authenticated. Please sign in.")
