'''Index Management page of the Streamlit app.'''

import os
import traceback
import streamlit as st
from utilities.helper import LLMHelper
from utilities.authenticate import set_st_auth_vars
from utilities.pagehandler import delete_page, all_pages

def delete_embedding():
    'Function to delete an embedding'
    llm_helper.vector_store.delete_keys([f"{st.session_state['embedding_to_drop']}"])

def delete_file():
    'Function to delete all the files'
    embeddings_to_delete = data[data.filename == st.session_state['file_to_drop']].key.tolist()
    embeddings_to_delete = list(map(lambda x: f"{x}", embeddings_to_delete))
    llm_helper.vector_store.delete_keys(embeddings_to_delete)

def delete_all():
    'Function to delete all the embeddings'
    embeddings_to_delete = data.key.tolist()
    embeddings_to_delete = list(map(lambda x: f"{x}", embeddings_to_delete))
    llm_helper.vector_store.delete_keys(embeddings_to_delete)

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
        llm_helper = LLMHelper()

        # Query RediSearch to get all the embeddings
        data = llm_helper.get_all_documents(k=1000)

        if len(data) == 0:
            st.warning("No embeddings found. Go to the 'Add Document' tab to insert your docs.")
        else:
            st.dataframe(data, use_container_width=True)

            st.download_button("Download data",
                               data.to_csv(index=False).encode('utf-8'),
                               "embeddings.csv",
                               "text/csv",
                               key='download-embeddings')

            st.text("")
            st.text("")
            col1, col2, col3, col4 = st.columns([3,2,2,1])
            with col1:
                st.selectbox("Embedding id to delete",
                             data.get('key',[]),
                             key="embedding_to_drop")
            with col2:
                st.text("")
                st.text("")
                st.button("Delete embedding", on_click=delete_embedding)
            with col3:
                st.selectbox("File name to delete",
                             set(data.get('filename',[])),
                             key="file_to_drop")
            with col4:
                st.text("")
                st.text("")
                st.button("Delete file", on_click=delete_file)

            st.text("")
            st.text("")
            st.button("Delete all embeddings", on_click=delete_all, type="secondary")

    # pylint: disable=broad-except
    except Exception:
        st.error(traceback.format_exc())
elif not st.session_state["authenticated"]:
    st.write("You are not authorized to view this page.")
else:
    for page in all_pages:
        delete_page(__file__, page)
    st.write("You are not authenticated. Please sign in.")
