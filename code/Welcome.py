from dotenv import load_dotenv
load_dotenv()

import os
import streamlit as st
from utilities.authenticate import set_st_auth_vars
from utilities.pagehandler import add_page, delete_page, all_pages, user_pages, admin_pages
import logging
logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)

for page in all_pages:
    delete_page(__file__, page)

# Set page layout to wide screen and menu item
menu_items = {
'Get help': None,
'Report a bug': None,
'About': '''
    ## Embeddings App
    Azure OpenAI Service based Private Chat Application.
'''
}

st.set_page_config(
    page_title="Private Chat Application",
    page_icon="🧠",
    layout="wide",
    menu_items=menu_items)
set_st_auth_vars()

col1, col2 = st.columns([1,3])
with col1:
    st.image(os.path.join('images','microsoft.png'))
with col2:
    st.text('')
    st.header(':blue[Azure OpenAI Service] - Private Chat')

if 'authenticated' in st.session_state and st.session_state['authenticated']:
    if os.getenv('AAD_General_SG') in st.session_state['user_groups']:
        print('Logged in as regular user')
        for page in user_pages:
            add_page(__file__, page)
    if os.getenv('AAD_Admin_SG') in st.session_state['user_groups']:
        print('Logged in as admin user')
        for page in admin_pages:
            add_page(__file__, page)
else:
    for page in all_pages:
        delete_page(__file__, page)
    st.write("You are not authenticated. Please sign in.")
