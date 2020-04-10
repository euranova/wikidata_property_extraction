"""Class for second order."""
import logging

import pandas as pd

from wikidata_property_extraction import translation

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SecondOrder():
    """Class.

    The goal of SecondOrder is to translate a set or all the instances of an
    ontology (identified by its wikidata property ID)
    by adding some links to external ontologies.
    This class takes a main property ID, a DataFrame of links between
    ontologies, a dictionary to link the name of the external ontologies
    to WikiData properties and a list of target languages.
    """

    def __init__(self, main_property_id, links_df, dict_properties,
                 languages_list, limit=5000, all_elem=True,
                 nb_elems_values=100, url='https://query.wikidata.org/sparql'):
        """Init function of SecondOrder class.

        Args:
            main_property_id (int): id of the main property.
            links_df (pd.DataFrame): DataFrame with the links between the
                different ontologies. The expected format is columns named:
                ['value_property', 'id_auxiliary', 'name_auxiliary']
            dict_properties (dict): Dictionnary of the links between the name
                of the external ontologies and the corresponding proporties in
                WikiData. Format: 'ontology_name': 'wikidata_id'.
            languages_list (list): list of all the languages we want a
                translation, using the format defined by WikiData (cf.
                https://www.wikidata.org/wiki/Help:Wikimedia_language_codes/lists/all)
            limit (int, optional): the number of elements returned in one
                query. An higher number could improve the speed but as the
                queries are limited in time by Wikidata, would also lead to
                a bigger chance to fail. Defaults to 5000.
            all_elem (bool, optional): a flag, True if extracts all the label
                of the main property, False is the extraction is only for the
                IDs in the links_df DataFrame. Defauts to True.
            nb_elems_values (int, optional): number of elements put in VALUES,
                small number to avoid error 414.
            url (str, optional): url to wikidata or to a local sparql endpoint
                of wikidata. Defaults to 'https://query.wikidata.org/sparql'.

        """
        mandatory_columns = ['value_property', 'id_auxiliary',
                             'name_auxiliary']
        if not all([column in links_df.columns
                    for column in mandatory_columns]):
            error_str = (f'Not all mandatory columns were found in links_df:'
                         + f'{str(mandatory_columns)} are all necessary.')
            logger.error(error_str)
            raise AttributeError(error_str)
        links_df = links_df.astype(str)
        self._main_property_id = main_property_id
        self._links_df = links_df
        self._dict_properties = dict_properties
        self._languages_list = languages_list
        self._limit = limit
        self._all_elem = all_elem
        self._nb_elems_values = nb_elems_values
        self._url = url

    @property
    def main_property_id(self):
        """Getter of main_property_id."""
        return self._main_property_id

    @main_property_id.setter
    def main_property_id(self, main_property_id):
        """Setter for main_property_id.

        Args:
            main_property_id (string): the WikiData id of of the main property.

        """
        self._main_property_id = str(main_property_id)

    @property
    def links_df(self):
        """Getter of links_df."""
        return self._links_df

    @links_df.setter
    def links_df(self, links_df):
        """Setter for links_df.

        Args:
            links_df (pd.DataFrame): DataFrame with the links between the
                different ontologies. The exected format is:
                ['main_prop_value', 'other_prop_value', 'name_extern_ontology']
                for each line.

        """
        self._links_df = links_df

    @property
    def dict_properties(self):
        """Getter of dict_properties."""
        return self._dict_properties

    @dict_properties.setter
    def dict_properties(self, dict_properties):
        """Setter for dict_properties.

        Args:
            dict_properties (dict): Dictionnary of the links between the name
                of the external ontologies and the corresponding proporties in
                WikiData. Format: 'ontology_name': 'wikidata_id'.

        """
        self._dict_properties = dict_properties

    @property
    def languages_list(self):
        """Getter of languages_list."""
        return self._languages_list

    @languages_list.setter
    def languages_list(self, languages_list):
        """Setter function for languages_list.

        Args:
            languages_list (list): a list of string with the languages.

        """
        self._languages_list = languages_list

    @property
    def limit(self):
        """Getter of limit."""
        return self._limit

    @limit.setter
    def limit(self, limit):
        """Setter function for limit.

        Args:
            limit (int): the maximum number of entities requested in one query.

        """
        self._limit = limit

    @property
    def all_elem(self):
        """Getter of all_elem."""
        return self._all_elem

    @all_elem.setter
    def all_elem(self, all_elem):
        """Setter function for all_elem.

        Args:
            all_elem (bool): the function returns the translation
                obtained of all the elements with the properties if True, else
                returns only the elemnts with the value which are in links_df.
                Defaults to True.

        """
        self._all_elem = all_elem

    @property
    def nb_elems_values(self):
        """Getter of nb_elems_values."""
        return self._nb_elems_values

    @nb_elems_values.setter
    def nb_elems_values(self, nb_elems_values):
        """Setter function for nb_elems_values.

        Args:
            nb_elems_values (int): the maximum number elements put in the
                VALUES part of the query. A number too big could bug because
                of the error 414: Request-URI too long.

        """
        self._nb_elems_values = nb_elems_values

    @property
    def url(self):
        """Getter of url."""
        return self._url

    @url.setter
    def url(self, url):
        """Setter function for limit.

        Args:
            url (string): the url of the wikidata endpoint.

        """
        self._url = url

    def __get_list_elem_prop(self, prop):
        """List the elements of the property in links_df.

        Args:
            prop (string): A WikiData property.

        Returns:
            np.array: array with all the elements of prop.

        """
        if prop == self._main_property_id:
            column = 'value_property'
            elem_list = self._links_df[column].unique()
        else:
            column = 'name_auxiliary'
            prop_name = self._dict_properties[prop]
            prop_df = self._links_df[self._links_df[column] == prop_name]
            logger.debug(prop_df)
            elem_list = prop_df['id_auxiliary'].unique()

        return elem_list

    def __get_translations(self, prop, is_main=False):
        """Get the translations of a given property.

        Args:
            prop (string): A WikiData property.
            is_main (bool): a flag to say whether the property is the main one
                or not.

        Returns:
            pd.DataFrame: a DataFrame with the translations of the elements of
                the property.

        """
        if is_main and self._all_elem:
            translator = translation.Translator(
                prop, self._languages_list, limit=self._limit,
                nb_elems_values=self._nb_elems_values, url=self._url
            )
            results_df = translator.translate()
        else:
            elem_list = self.__get_list_elem_prop(prop)
            translator = translation.Translator(
                prop, self._languages_list, limit=self._limit,
                nb_elems_values=self._nb_elems_values, url=self._url
            )
            results_df = translator.translate(elem_list)

        return results_df

    def translate(self):
        """translate.

        Public function to launch the queries for second order
        extraction.

        Returns:
            pd.DataFrame: containing all the labels and alternative
                labels of the entities with the given property in the
                languages. Columns: ['entity', 'value_property',
                ('labelLang', 'altLang') with Lang in languages_list,
                id_auxiliary, name_auxiliary, source_degree]

        """
        # First translation of the main property

        main_translations_df = self.__get_translations(self._main_property_id,
                                                       True)
        logger.info('Translations of the main property obtained')
        main_translations_df['source_degree'] = 'First'
        logger.debug(main_translations_df)
        auxiliary_translations_df = pd.DataFrame()
        # Then get the translations of the other properties
        for property_id, property_name in self._dict_properties.items():
            logger.info('Starting the query for the property {}'
                        .format(property_name))
            property_translations_df = self.__get_translations(property_id)

            property_translations_df = \
                property_translations_df.rename({'value_property':
                                                 'id_auxiliary'},
                                                axis=1)
            links_df = self._links_df[self._links_df['name_auxiliary'] ==
                                      property_name]
            logger.debug(property_translations_df)
            property_translations_df = \
                property_translations_df.merge(links_df, how='inner',
                                               on='id_auxiliary')
            auxiliary_translations_df = \
                pd.concat([auxiliary_translations_df,
                           property_translations_df],
                          ignore_index=True, sort=True)

        auxiliary_translations_df['source_degree'] = 'Second'

        logger.info('The translations of all the properties have ' +
                    'been obtained.')

        translations_df = pd.concat([main_translations_df,
                                     auxiliary_translations_df],
                                    ignore_index=True, sort=True)

        translations_df = translations_df.drop_duplicates()

        return translations_df
