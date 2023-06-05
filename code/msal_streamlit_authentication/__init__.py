'''Streamlit component for Microsoft Authentication Library (MSAL) authentication.'''
import os
from pathlib import Path
import streamlit.components.v1 as components

COMPONENT_NAME = "msal_authentication"

BUILD_DIR = str(Path(__file__).parent / "frontend" / "dist")
_component_func = components.declare_component(name=COMPONENT_NAME, path=BUILD_DIR)


def msal_authentication( auth, cache, login_request=None, logout_request=None):
    'Function to add MSAL authentication to a Streamlit app'
    authenticated_user_profile = _component_func(
        auth=auth,
        cache=cache,
        login_request=login_request,
        logout_request=logout_request,
        login_button_text='Login',
        logout_button_text='Logout',
        class_name='authenticator_component',
        html_id='authenticator_button',
        default=None,
        key=1
    )
    return authenticated_user_profile
