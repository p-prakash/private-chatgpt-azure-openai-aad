'''Document Viewer Page of the Streamlit App.'''

import os
import traceback
import streamlit as st
from utilities.helper import LLMHelper
from utilities.authenticate import set_st_auth_vars
from utilities.pagehandler import delete_page, all_pages

# Set page layout to wide screen and menu item
menu_items = {
    'Get help': None,
    'Report a bug': None,
    'About': '''
    ## Embeddings App
    Embedding testing application.
    '''
}
st.set_page_config(layout="wide", menu_items=menu_items)
set_st_auth_vars()

if os.getenv('AAD_Admin_SG') in st.session_state["user_groups"]:
    try:
        HIDE_STREAMLIT_STYLE = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    </style>
                    """
        st.markdown(HIDE_STREAMLIT_STYLE, unsafe_allow_html=True)
        llm_helper = LLMHelper()
        col1, col2, col3 = st.columns([2,1,1])
        files_data = llm_helper.blob_client.get_all_files()
        st.dataframe(files_data, use_container_width=True)

    # pylint: disable=broad-except
    except Exception as e:
        st.error(traceback.format_exc())
elif not st.session_state["authenticated"]:
    st.write("You are not authorized to view this page.")
else:
    for page in all_pages:
        delete_page(__file__, page)
    st.write("You are not authenticated. Please sign in.")
