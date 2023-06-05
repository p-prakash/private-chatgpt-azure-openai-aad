'''Module for handling pages in the app'''

from pathlib import Path
from streamlit.util import calc_md5
from streamlit.source_util import (
    page_icon_and_name,
    # calc_md5,
    get_pages,
    _on_pages_changed
)

all_pages = [
                'Internal_ChatGPT',
                'Add_Document',
                'Document_Viewer',
                'Index_Management',
                'Utils_-_Document_Summary',
                'Utils_-_Conversation_Data_Extraction',
                'Utils_-_Prompt_Exploration',
                'Private_ChatGPT'
            ]
user_pages = [
                '00_Internal_ChatGPT',
                '10_Utils - Document_Summary',
                '11_Utils - Conversation_Data_Extraction',
                '12_Utils - Prompt Exploration',
                '20_Private_ChatGPT.py'
            ]
admin_pages = [
                '00_Internal_ChatGPT',
                '01_Add_Document',
                '03_Document_Viewer',
                '04_Index_Management',
                '10_Utils - Document_Summary',
                '11_Utils - Conversation_Data_Extraction',
                '12_Utils - Prompt Exploration',
                '20_Private_ChatGPT.py'
            ]

def delete_page(main_script_path_str, page_name):
    'Delete a page from the app'
    current_pages = get_pages(main_script_path_str)
    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break

    _on_pages_changed.send()

def add_page(main_script_path_str, page_name):
    'Add a page to the app'
    pages = get_pages(main_script_path_str)
    main_script_path = Path(main_script_path_str)
    pages_dir = main_script_path.parent / 'pages'
    script_path = [f for f in list(pages_dir.glob('*.py'))+list(main_script_path.parent.glob('*.py')) if f.name.find(page_name) != -1][0]
    script_path_str = str(script_path.resolve())
    pi, pn = page_icon_and_name(script_path)
    psh = calc_md5(script_path_str)
    pages[psh] = {
        "page_script_hash": psh,
        "page_name": pn,
        "icon": pi,
        "script_path": script_path_str,
    }
    _on_pages_changed.send()
