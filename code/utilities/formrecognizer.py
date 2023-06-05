'''Helper functions for Azure Form Recognizer'''

import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

class AzureFormRecognizerClient:
    'Helper functions for Azure Form Recognizer'
    def __init__(self, form_recognizer_endpoint: str = '', form_recognizer_key: str = ''):
        'Initialize the class'
        load_dotenv()

        self.pages_per_embeddings = int(os.getenv('PAGES_PER_EMBEDDINGS', 2))
        self.section_to_exclude = ['footnote', 'pageHeader', 'pageFooter', 'pageNumber']

        #pylint: disable=line-too-long
        self.form_recognizer_endpoint : str = form_recognizer_endpoint if form_recognizer_endpoint else os.getenv('FORM_RECOGNIZER_ENDPOINT')
        #pylint: disable=line-too-long
        self.form_recognizer_key : str = form_recognizer_key if form_recognizer_key else os.getenv('FORM_RECOGNIZER_KEY')

    def analyze_read(self, form_url):
        'Analyze the document and return the text'
        document_analysis_client = DocumentAnalysisClient(
            endpoint=self.form_recognizer_endpoint,
            credential=AzureKeyCredential(self.form_recognizer_key)
        )

        poller = document_analysis_client.begin_analyze_document_from_url(
                "prebuilt-layout", form_url)
        layout = poller.result()

        results = []
        # page_result = ''
        for doc_p in layout.paragraphs:
            page_number = doc_p.bounding_regions[0].page_number
            output_file_id = int((page_number - 1 ) / self.pages_per_embeddings)

            if len(results) < output_file_id + 1:
                results.append('')

            if doc_p.role not in self.section_to_exclude:
                results[output_file_id] += f"{doc_p.content}\n"

        for doc_t in layout.tables:
            page_number = doc_t.bounding_regions[0].page_number
            output_file_id = int((page_number - 1 ) / self.pages_per_embeddings)

            if len(results) < output_file_id + 1:
                results.append('')
            previous_cell_row=0
            rowcontent='| '
            tablecontent = ''
            for doc_c in doc_t.cells:
                if doc_c.row_index == previous_cell_row:
                    rowcontent += doc_c.content + " | "
                else:
                    tablecontent += rowcontent + "\n"
                    rowcontent='|'
                    rowcontent += doc_c.content + " | "
                    previous_cell_row += 1
            results[output_file_id] += f"{tablecontent}|"
        return results
