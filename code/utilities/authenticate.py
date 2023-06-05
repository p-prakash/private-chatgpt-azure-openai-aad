'''Authenticate user and set session state variables'''

import os
from dotenv import load_dotenv
import streamlit as st
from msal_streamlit_authentication import msal_authentication

load_dotenv()

def set_st_auth_vars():
    'Autehnticate user and set session state variables'
    login_token = msal_authentication(
        auth={
            'clientId': os.getenv('AAD_ClietnId'),
            'authority': os.getenv('AAD_Authority'),
            'redirectUri': os.getenv('AAD_Redirect_URL'),
            'postLogoutRedirectUri': os.getenv('AAD_Redirect_URL')
        },
        cache={
            'cacheLocation': 'sessionStorage',
            'storeAuthStateInCookie': False
        },
        login_request={
            'scopes': [os.getenv('AAD_Scope')]
        },
        logout_request={}
    )

    st.session_state['user_groups'] = []

    if login_token is not None:
        st.session_state['authenticated'] = True
        st.session_state['user_groups'] = login_token['idTokenClaims']['groups']
        st.write(f"Welcome {login_token['idTokenClaims']['name']}!")
    else:
        st.session_state['authenticated'] = False
