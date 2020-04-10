"""Test for postprocess.py"""
import os

import pandas as pd

from wikidata_property_extraction import postprocess


def test_translations_only_translation():
    """End to end test of translations_only.

    End to end test of translations_only with a results_df
    from translations.

    """
    path_file = os.path.dirname(os.path.realpath(__file__))
    path_json = os.path.join(path_file, 'test_translations_only_input.json')
    with open(path_json, 'rb') as input_json:
        input_df = pd.read_json(input_json)

    path_json = os.path.join(path_file, 'test_translations_only_output.json')
    with open(path_json, 'rb') as output_json:
        output_df = pd.read_json(output_json)

    ouput_test_df = postprocess.translations_only(input_df)

    assert ouput_test_df.equals(output_df)
