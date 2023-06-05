'''Conversation Data Extraction page of the Streamlit app.'''

import os
import traceback
import streamlit as st
from utilities.helper import LLMHelper
from utilities.authenticate import set_st_auth_vars
from utilities.pagehandler import delete_page, all_pages

def clear_summary():
    'Clear the summaries'
    st.session_state['summary'] = ''

def get_custom_prompt():
    'Get the prompt based on the input'
    customtext = st.session_state['customtext']
    customprompt = f"{customtext}"
    return customprompt

def customcompletion():
    'Custom completion of the provided text'
    response = llm_helper.get_completion(get_custom_prompt())
    st.session_state['conv_result'] = response.encode().decode()

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

if os.getenv('AAD_General_SG') in st.session_state["user_groups"] or \
    os.getenv('AAD_Admin_SG') in st.session_state["user_groups"]:
    try:
        llm_helper = LLMHelper()

        st.markdown('## Conversation data extraction')

        CONVERSATION_PROMPT = """
User: Hi there, I'm off between August 25 and September 11. \
I saved up 4000 for a nice trip. If I flew out from San Francisco, what are your \
suggestions for where I can go?
Agent: For that budget you could travel to cities in the US, Mexico, Brazil, Italy \
or Japan. Any preferences?
User: Excellent, I've always wanted to see Japan. What kind of hotel can I expect?
Agent: Great, let me check what I have. First, can I just confirm with you that this \
is a trip for one adult?
User: Yes it is
Agent: Great, thank you, In that case I can offer you 15 days at HOTEL Sugoi, a 3 star \
hotel close to a Palace. You would be staying there between August 25th and September 7th. \
They offer free wifi and have an excellent guest rating of 8.49/10. \
The entire package costs 2024.25USD. Should I book this for you?
User: That sounds really good actually. Lets say I have a date I wanted to bring…would \
Japan be out of my price range then?
Agent: Yes, unfortunately the packages I have for two in Japan do not fit in your budget. \
However I can offer you a 13 day beach getaway at the 3 star Rose Sierra Hotel in Santo Domingo. \
Would something like that interest you?
User: How are the guest ratings for that place?
Agent: 7.06/10, so guests seem to be quite satisfied with the place.
User: TRUE. You know what, I'm not sure that I'm ready to ask her to travel with me yet anyway. \
Just book me for Sugoi
Agent:I can do that for you! 
User:Thanks!
Agent: Can I help you with some other booking today?
User:No, thanks!
Execute these tasks:
-	Summarize the conversation, key: summary
-      Customer budget none if not detected, key: budget
-      Departure city, key: departure
-      Destination city, key: destination
-      Selected country, key: country
-      Which hotel the customer choose?, key: hotel
-	Did the agent remind the customer about the evaluation survey? , key:evaluation true or \
false as bool
-	Did the customer mention a product competitor?, key: competitor true or false as bool
-	Did the customer ask for a discount?, key:discount true or false as bool
- Agent asked for additional customer needs. key: additional_requests
- Was the customer happy with the resolution? key: satisfied
Answer in JSON machine-readable format, using the keys from above.
Format the ouput as JSON object called "results". Pretty print the JSON and make sure that \
is properly closed at the end.
"""

        # displaying a box for a custom prompt
        st.session_state['customtext'] = st.text_area(label='Prompt',
                                                      value=CONVERSATION_PROMPT,
                                                      height=400)
        st.button(label='Execute tasks', on_click=customcompletion)
        # displaying the summary
        RESULT = ''
        if 'conv_result' in st.session_state:
            RESULT = st.session_state['conv_result']
        st.text_area(label='OpenAI result', value=RESULT, height=200)

    # pylint disable=broad-except
    except Exception:
        st.error(traceback.format_exc())
elif not st.session_state['authenticated']:
    st.write('You are not authorized to view this page.')
else:
    for page in all_pages:
        delete_page(__file__, page)
    st.write('You are not authenticated. Please sign in.')
