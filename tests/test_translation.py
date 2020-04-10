"""Testing translation.py."""
import pandas as pd

from wikidata_property_extraction import translation, header

USER_AGENT_TEST = 'WikidataExtractionPythonTest/0.1 '\
    + '(wikidata_extraction@euranova.eu)'
header.initialize_user_agent(USER_AGENT_TEST)


def test_error_429():
    """Test if error 429 coming from too many requests are handled."""
    translator = translation.Translator('P2586', ['fr'], limit=5)
    result_df = translator.translate()
    assert isinstance(result_df, pd.DataFrame)


def test_end_to_end_full():
    """Test if end to end is working."""
    translator = translation.Translator('P699', ['es', 'fr'])
    result_df = translator.translate()
    assert isinstance(result_df, pd.DataFrame)


def test_subqueries():
    """Test if multiquery and single query of the same data find the same."""
    translator = translation.Translator('P2586', ['fr'])
    result_solo_query_df = translator.translate().sort_values('entity')
    result_solo_query_df = result_solo_query_df.reset_index(drop=True)
    result_solo_query_df = result_solo_query_df[['entity', 'value_property']]
    translator.limit = 20
    result_multi_query_df = translator.translate().sort_values('entity')
    result_multi_query_df = result_multi_query_df.reset_index(drop=True)
    result_multi_query_df = result_multi_query_df[['entity', 'value_property']]
    assert result_solo_query_df.equals(result_multi_query_df)


def test_end_to_end_list():
    """Test if IDListTranslator works end to end."""
    translator = translation.Translator('P2586', ['en', 'fr'])
    result_df = translator.translate(id_list=['01', '02', '03', '04'])
    assert isinstance(result_df, pd.DataFrame)
