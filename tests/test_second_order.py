"""Testing second-order.py."""
import logging
import os

import pandas as pd

from wikidata_property_extraction import second_order, header

USER_AGENT_TEST = 'WikidataExtractionPythonTest/0.1 '\
    + '(wikidata_extraction@euranova.eu)'
header.initialize_user_agent(USER_AGENT_TEST)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def test_end_to_end():
    """Testing end-to-end second-order queries."""
    path_file = os.path.dirname(os.path.realpath(__file__))
    path_json = os.path.join(path_file, 'links_df_test.json')
    with open(path_json, 'rb') as links_json:
        links_df = pd.read_json(links_json)
    dict_prop = {'P486': 'MeSH', 'P492': 'OMIM', 'P2892': 'UMLS',
                 'P672': 'MeSH', 'P6694': 'MeSH', 'P6680': 'MeSH'}
    translator = second_order.SecondOrder('P699', links_df, dict_prop,
                                          ['cs', 'it'], all_elem=False)

    results_df = translator.translate()
    assert isinstance(results_df, pd.DataFrame)
    assert 'Second' in results_df['source_degree'].unique()


def test_no_first():
    """Testing when no first-order results."""
    path_file = os.path.dirname(os.path.realpath(__file__))
    path_json = os.path.join(path_file, 'links_df_test_no_result.json')
    with open(path_json, 'rb') as links_json:
        links_df = pd.read_json(links_json)
    dict_prop = {'P486': 'MeSH', 'P492': 'OMIM', 'P2892': 'UMLS',
                 'P672': 'MeSH', 'P6694': 'MeSH', 'P6680': 'MeSH'}
    translator = second_order.SecondOrder('P699', links_df, dict_prop,
                                          ['cs', 'it'], all_elem=False)
    results_df = translator.translate()
    assert isinstance(results_df, pd.DataFrame)
    assert 'First' not in results_df['source_degree'].unique()
