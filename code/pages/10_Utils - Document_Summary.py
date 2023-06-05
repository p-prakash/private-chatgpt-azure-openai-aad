'''Document Summary page for the Embeddings App'''

import os
import traceback
import streamlit as st
from utilities.helper import LLMHelper
from utilities.authenticate import set_st_auth_vars
from utilities.pagehandler import delete_page, all_pages


def summarize():
    'Summarize the provided text'
    response = llm_helper.get_completion(get_prompt())
    st.session_state['summary'] = response

def clear_summary():
    'Clear the summaries'
    st.session_state['summary'] = ""

def get_prompt():
    'Get the prompt based on the input'
    text = st.session_state['text']
    if text is None or text == '':
        text = '{}'
    if summary_type == "Basic Summary":
        prompt = f'Summarize the following text:\n\n{text}\n\nSummary:'
    elif summary_type == "Bullet Points":
        prompt = f'Summarize the following text into bullet points:\n\n{text}\n\nSummary:'
    elif summary_type == "Explain it to a second grader":
        prompt = f'Explain the following text to a second grader:\n\n{text}\n\nSummary:'
    return prompt

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

if os.getenv('AAD_General_SG') in st.session_state['user_groups'] or \
    os.getenv('AAD_Admin_SG') in st.session_state['user_groups']:
    try:
        llm_helper = LLMHelper()

        st.markdown('## Summarization')
        # radio buttons for summary type
        summary_type = st.radio(
            'Select a type of summarization',
            ['Basic Summary', 'Bullet Points', 'Explain it to a second grader'],
            key='visibility'
        )
        # text area for user to input text
        INPUT_TEXT = 'A neutron star is the collapsed core of a massive supergiant star,' +\
                        'which had a total mass of between 10 and 25 solar masses, possibly ' +\
                        'more if the star was especially metal-rich.[1] Neutron stars are the ' +\
                        'smallest and densest stellar objects, excluding black holes and ' +\
                        'hypothetical white holes, quark stars, and strange stars.[2] Neutron ' +\
                        'stars have a radius on the order of 10 kilometres (6.2 mi) and a mass ' +\
                        'of about 1.4 solar masses.[3] They result from the supernova ' +\
                        'explosion of a massive star, combined with gravitational collapse, ' +\
                        'that compresses the core past white dwarf star density to that of ' +\
                        'atomic nuclei.'
        st.session_state['text'] = st.text_area(
                                    label="Enter some text to summarize",
                                    value=INPUT_TEXT,
                                    height=200)
        st.button(label="Summarize", on_click=summarize)

        # if summary doesn't exist in the state, make it an empty string
        SUMMARY = ""
        if 'summary' in st.session_state:
            SUMMARY = st.session_state['summary']

        # displaying the summary
        st.text_area(label="Summary result", value=SUMMARY, height=200)
        st.button(label="Clear summary", on_click=clear_summary)

        # displaying the prompt that was used to generate the summary
        st.text_area(label="Prompt",value=get_prompt(), height=400)
        st.button(label="Summarize with updated prompt")

    # pylint: disable=broad-except
    except Exception as e:
        st.error(traceback.format_exc())
elif not st.session_state["authenticated"]:
    st.write("You are not authorized to view this page.")
else:
    for page in all_pages:
        delete_page(__file__, page)
    st.write("You are not authenticated. Please sign in.")
