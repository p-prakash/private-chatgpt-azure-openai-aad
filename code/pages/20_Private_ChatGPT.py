'''Private Chat GPT page of the Streamlit app.'''

import os
import traceback
import logging
import streamlit as st
from utilities.authenticate import set_st_auth_vars
from utilities.helper import LLMHelper
from utilities.pagehandler import delete_page, all_pages
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(
                            logging.WARNING)

def check_deployment():
    'Function to check whether the deployment is working.'
    # Check if the deployment is working
    #\ 1. Check if the llm is working
    try:
        llm_helper_local = LLMHelper()
        llm_helper_local.get_completion('Generate a joke!')
        st.success('LLM is working!')
    #pylint: disable=broad-except
    except Exception:
        error_msg = f'''
LLM is not working.
Please check you have a deployment name {llm_helper_local.deployment_name} \
in your Azure OpenAI resource {llm_helper_local.api_base}.
If you are using an Instructions based deployment (text-davinci-003), \
please check you have an environment variable OPENAI_DEPLOYMENT_TYPE=Text \
or delete the environment variable OPENAI_DEPLOYMENT_TYPE.
If you are using a Chat based deployment (gpt-35-turbo or gpt-4-32k or gpt-4), \
please check you have an environment variable OPENAI_DEPLOYMENT_TYPE=Chat.
Then restart your application.
'''
        st.error(error_msg)
        st.error(traceback.format_exc())
    #\ 2. Check if the embedding is working
    try:
        llm_helper_local = LLMHelper()
        llm_helper_local.embeddings.embed_documents(texts=['This is a test'])
        st.success('Embedding is working!')
    #pylint: disable=broad-except
    except Exception:
        error_msg = f'''
Embedding model is not working.
Please check you have a deployment named "text-embedding-ada-002" for \
"text-embedding-ada-002" model in your Azure OpenAI resource {llm_helper_local.api_base}.
Then restart your application.
'''
        st.error(error_msg)
        st.error(traceback.format_exc())
    #\ 3. Check if the translation is working
    try:
        llm_helper_local = LLMHelper()
        llm_helper_local.translator.translate('This is a test', 'nl')
        st.success('Translation is working!')
    #pylint: disable=broad-except
    except Exception:
        st.error('''Translation model is not working.
            Please check your Azure Translator key in the App Settings.
            Then restart your application.
            ''')
        st.error(traceback.format_exc())
    #\ 4. Check if the Redis is working with previous version of data
    try:
        llm_helper_local = LLMHelper()
        if llm_helper_local.vector_store_type != 'AzureSearch':
            if llm_helper_local.vector_store.check_existing_index('embeddings-index'):
                error_msg = '''
Seems like you're using a Redis with an old data structure.  
If you want to use the new data structure, you can start using the app and go to "Add Document" \
-> "Add documents in Batch" and click on "Convert all files and add embeddings" to reprocess \
your documents.
To remove this working, please delete the index "embeddings-index" from your Redis.
                '''
                st.warning(error_msg)
            else:
                st.success('Redis is working!')
        else:
            try:
                llm_helper_local.vector_store.index_exists()
                st.success('Azure Cognitive Search is working!')
            #pylint: disable=broad-except
            except Exception:
                st.error('''Azure Cognitive Search is not working.
                    Please check your Azure Cognitive Search service name and service key in the App Settings.
                    Then restart your application.
                    ''')
                st.error(traceback.format_exc())
    #pylint: disable=broad-except
    except Exception:
        st.error('''Redis is not working.
            Please check your Redis connection string in the App Settings.
            Then restart your application.
            ''')
        st.error(traceback.format_exc())


def check_variables_in_prompt():
    'Function to check whether the prompt contains the variables "{summaries}" and "{question}".'
    # Check if "summaries" is present in the string custom_prompt
    if '{summaries}' not in st.session_state.custom_prompt:
        st.warning('''Your custom prompt doesn't contain the variable "{summaries}".
        This variable is used to add the content of the documents retrieved from \
the VectorStore to the prompt.
        Please add it to your custom prompt to use the app.
        Reverting to default prompt.
        ''')
        st.session_state.custom_prompt = ""
    if '{question}' not in st.session_state.custom_prompt:
        st.warning('''Your custom prompt doesn't contain the variable "{question}".
        This variable is used to add the user's question to the prompt.
        Please add it to your custom prompt to use the app.
        Reverting to default prompt.
        ''')
        st.session_state.custom_prompt = ""

@st.cache_data()
def get_languages():
    'Function to get the available languages from the Azure Translator.'
    return llm_helper.translator.get_available_languages()

# Set page layout to wide screen and menu item
menu_items = {
'Get help': None,
'Report a bug': None,
'About': '''
    ## Embeddings App
    Embedding testing application.
'''
}

st.set_page_config(layout='wide', menu_items=menu_items)

set_st_auth_vars()

if os.getenv('AAD_Admin_SG') in st.session_state['user_groups']:
    try:
        # default_prompt = ''
        DEFAULT_QUESTION = ''
        DEFAULT_ANSWER = ''

        if 'question' not in st.session_state:
            st.session_state['question'] = DEFAULT_QUESTION
        if 'response' not in st.session_state:
            st.session_state['response'] = DEFAULT_ANSWER
        if 'context' not in st.session_state:
            st.session_state['context'] = ''
        if 'custom_prompt' not in st.session_state:
            st.session_state['custom_prompt'] = ''
        if 'custom_temperature' not in st.session_state:
            st.session_state['custom_temperature'] = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))

        llm_helper = LLMHelper(custom_prompt=st.session_state.custom_prompt,
                               temperature=st.session_state.custom_temperature)

        # Get available languages for translation
        available_languages = get_languages()

        # Custom prompt variables
        CUSTOM_PROMPT_PLACEHOLDER = '''{summaries}
Please reply to the question using only the text above.  
Question: {question}  
Answer:'''
        CUSTOM_PROMPT_HELP = '''You can configure a custom prompt by adding the variables \
{summaries} and {question} to the prompt.  
{summaries} will be replaced with the content of the documents retrieved from the VectorStore.  
{question} will be replaced with the user's question.
'''

        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            st.image(os.path.join('images','microsoft.png'))

        col1, col2, col3 = st.columns([2,2,2])
        with col1:
            st.button('Check deployment', on_click=check_deployment)
        with col3:
            with st.expander('Settings'):
                # model = st.selectbox(
                #     "OpenAI GPT-3 Model",
                #     [os.environ['OPENAI_ENGINE']]
                # )
                # st.tokens_response = st.slider("Tokens response length", 100, 500, 400)
                st.slider('Temperature',
                          min_value=0.0,
                          max_value=1.0,
                          step=0.1,
                          key='custom_temperature')
                st.text_area('Custom Prompt',
                             key='custom_prompt',
                             on_change=check_variables_in_prompt,
                             placeholder= CUSTOM_PROMPT_PLACEHOLDER,
                             help=CUSTOM_PROMPT_HELP,
                             height=150)
                st.selectbox('Language',
                             [None] + list(available_languages.keys()),
                             key='translation_language')

        question = st.text_input('OpenAI Semantic Answer', DEFAULT_QUESTION)

        if question != '':
            st.session_state['question'] = question
            st.session_state['question'],\
            st.session_state['response'],\
            st.session_state['context'],\
            sources = llm_helper.get_semantic_answer_lang_chain(question, [])
            st.markdown('Answer:' + st.session_state['response'])
            st.markdown(f'\n\nSources: {sources}')
            with st.expander('Question and Answer Context'):
                st.markdown(st.session_state['context'].replace('$', '\$'))
                st.markdown(f'SOURCES: {sources}')

        if st.session_state['translation_language'] and \
            st.session_state['translation_language'] != '':
            st.write('Translation to other languages, 翻译成其他语言, النص باللغة العربية')
            st.write(llm_helper.translator.translate(
                            st.session_state['response'],
                            available_languages[st.session_state['translation_language']]))
    #pylint: disable=broad-except
    except Exception:
        st.error(traceback.format_exc())
elif not st.session_state["authenticated"]:
    st.write("You are not authorized to view this page.")
else:
    for page in all_pages:
        delete_page(__file__, page)
    st.write("You are not authenticated. Please sign in.")
