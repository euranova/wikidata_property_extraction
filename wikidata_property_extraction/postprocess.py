"""Methods to postprocess the results obtained with the module."""

import logging
import re

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _agg_removing_duplicates(agg_elem):
    """Aggregate while removing the duplicates.

    Aggregate the labels or alt labels together as a single element
    can have several Wikidata entities that need to be merged.

    Args:
        agg_elem (list of string): elem to aggregate

    Returns:
        string: aggregation with the deletion of the duplicates

    """
    str_elem = '|'.join(agg_elem)
    list_elem = str_elem.split('|')

    # Removing the name of WikiData when there is no labels in the languages
    regex = re.compile(r'Q[0-9]+')
    list_elem = [elem for elem in list_elem if not regex.match(elem)]

    list_elem_without_duplicates = list(set(list_elem))
    list_elem_without_duplicates.sort()
    elem_without_duplicates = '|'.join(list_elem_without_duplicates)

    return elem_without_duplicates


def translations_only(results_df):
    """Translations_only.

    Takes a DataFrame resulting of methods translate of Translator or
    SecondOrder of this module and extract only the translations of the
    elements.

    Args:
        results_df (pd.DataFrame): A pandas Dataframe containing the results
            of translation or second_order.

    Returns:
        pd.DataFrame: A pandas DataFrame with the columns
            ['value_property', 'labelLang', 'altLang']

    """
    columns = results_df.columns

    if 'value_property' not in columns:
        error_str = (f'The column value_property is mandatory in links_df')
        logger.error(error_str)
        raise AttributeError(error_str)

    drop_columns = ['entity']

    if 'id_auxiliary' in columns:
        drop_columns = drop_columns + ['id_auxiliary', 'name_auxiliary']

    if 'source_degree' in columns:
        drop_columns = drop_columns + ['source_degree']

    results_df = results_df.drop(drop_columns, axis=1)

    translations_only_df = \
        results_df.groupby('value_property').agg(_agg_removing_duplicates)

    return translations_only_df
