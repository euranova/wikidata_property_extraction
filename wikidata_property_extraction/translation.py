"""Translation class.

Allows to make query to Wikidata to obtain all the entities in several
languages.
"""
import json
import logging
import math
import time

import pandas as pd
import requests
from tqdm import tqdm

from wikidata_property_extraction import header

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Translator():
    """Translator class.

    Take a Wikidata property and a list of languages and returns either
    all the entities with the property in Wikidata or a list given in
    the languages requested.

    """

    def __init__(self, property_wiki, languages_list,
                 limit=5000, nb_elems_values=200,
                 url='https://query.wikidata.org/sparql'):
        """Init translator class.

        Args:
            property_wiki (string): the name of of the property in format
                'PXX'.
            languages_list (list): list of all the languages we want a
                translation, using the format defined by WikiData (cf.
                https://www.wikidata.org/wiki/Help:Wikimedia_language_codes/lists/all)
            limit (int, optional): the number of elements returned in one
                query. An higher number could improve the speed but as the
                queries are limited in time by Wikidata, would also lead to
                a bigger chance to fail. Defaults to 5000.
            nb_elems_values (int, optional): number of elements put in VALUES,
                small number to avoid error 414.
            url (str, optional): url to wikidata or to a local sparql endpoint
                of wikidata. Defaults to 'https://query.wikidata.org/sparql'.

        """
        self._property_wiki = str(property_wiki)
        self._languages_list = languages_list
        self._limit = int(limit)
        self._nb_elems_values = nb_elems_values
        self._url = url
        if header.user_agent is None:
            err_msg = 'You need to set a User-Agent before using the library.'\
                + 'Please use header.intialize_user_agent'
            logger.error(err_msg)
            raise ValueError(err_msg)

    @property
    def property_wiki(self):
        """Getter of property_wiki."""
        return self._property_wiki

    @property_wiki.setter
    def property_wiki(self, property_wiki):
        """Setter for property_wiki.

        Args:
            property_wiki (string): the name of of the property.

        """
        self._property_wiki = str(property_wiki)

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

    def _request_wikidata(self, query, retry=0):
        """Request_wikidata.

        Given a SPARQL query, make the request to Wikidata and return the
        json.

        Args:
            query (string): the SPARQL query.
            retry (int): the number of retries of the query. Defaults to 0.

        Raises:
            AssertionError: when the request fails.

        Returns:
            json: the result of the query.

        """
        logger.debug("Query sent to WikiData SPARQL endpoint.")
        logger.debug((self._url, query))

        # The user-agent is required for WikiData (rules here:
        # https://meta.wikimedia.org/wiki/User-Agent_policy)

        headers = {
            'User-Agent': header.user_agent
        }

        result = requests.get(self._url,
                              params={'format': 'json', 'query': query,
                                      'headers': headers},
                              stream=True)

        try:
            if result.status_code != 200:
                raise AssertionError
            try:
                result_json = result.json()
                result.close()
                logger.debug("Results have been obtained.")
            except json.JSONDecodeError as error:
                logger.error("The request have work but the result is not " +
                             "a json.")
                raise

        except AssertionError as error:
            if result.status_code == 429:
                if retry <= 2:
                    # An error 429 is a Too Many Request error, waiting before
                    # doing a new one is a solution to solve it. But, too many
                    # requests with this error could lead to a ban IP. So
                    # only 2 retry.
                    warn_msg = 'Error 429, waiting 60s before making '\
                        + 'the request again'
                    logger.warning(warn_msg)
                    time.sleep(60)
                    result_json = self._request_wikidata(query, retry+1)
                else:
                    err_msg = '3 straight errors 429, the IP could be ' \
                        + 'banned to request WikiData, stop retries.'
                    logger.error(err_msg)
                    raise AssertionError(err_msg)
            elif result.status_code == 403:
                err_msg = 'Error 403, your IP seems to have been banned from'\
                    + ' the WikiData SPARQL server. The ban is 24 hours long.'\
                    + f' The following error message has been received: '\
                    + f'{result.content}'
                logger.error(err_msg)
                raise AssertionError(err_msg)
            elif result.status_code == 414:
                err_msg = 'Error 414, the Request-URI is too long, reduce the'\
                    ' value of nb_entity_request in Translator and retry.'
                logger.error(err_msg)
                raise AssertionError(err_msg)
            else:
                err_msg = f'The request has failed with error code '\
                    + f'{result.status_code}. {result.content}'
                logger.error(err_msg)
                raise AssertionError(err_msg)

        return result_json

    @staticmethod
    def __format_id_list(id_list):
        """Format the list of id for the query.

        Args:
            id_list (list of string): list of the id in the current query.
        Returns:
            string: the query part for with the ids.

        """
        part_query = ['("' + str(current_id) + '")' for current_id in id_list]

        part_query = '\n'.join(part_query)

        return part_query

    def _format_subquery(self, offset):
        """Format part of the subquery.

        Args:
            offset (int): The current offset.

        Returns:
            str: part of the SPARQL subquery.

        """
        if self._id_list is not None:
            subquery = f'''
                    VALUES (?value_property){{
                        {self.__format_id_list(
                            self._id_list[offset:self._nb_elems_values
                                          + offset]
                        )}
                    }}
                }}ORDER BY ?entity
            '''
            return subquery
        else:
            subquery = f'''
                }}ORDER BY ?entity
                LIMIT {str(self._limit)} OFFSET {str(offset)}
            '''
            return subquery

    def _format_query(self, language, offset=0):
        """format_query.

        Format the SPARQL query for a given property_wiki and a given language.

        Args:
            language (string): the language of the current query result.
            offset (int, optional): offset of the query, useful if more
                entities than limit. Defaults to 0.

        Returns:
            string: the SPARQL query.

        """
        language_cap = language.capitalize()
        query = f'''
        SELECT ?entity ?value_property ?label{language_cap}
        (GROUP_CONCAT(?altBis{language_cap}; separator='|')
        AS ?alt{language_cap})
        WHERE {{
            {{
                SELECT ?entity ?value_property
                WHERE {{
                    ?entity wdt:{self._property_wiki} ?value_property .
                    {self._format_subquery(offset)}
            }}
            OPTIONAL {{
                ?entity skos:altLabel ?altBis{language_cap}.
                FILTER (lang(?altBis{language_cap})='{language}')
            }}
            SERVICE wikibase:label {{
                bd:serviceParam wikibase:language '{language}' .
                ?entity rdfs:label ?label{language_cap} .
            }}
        }} GROUP BY ?entity ?value_property ?label{language_cap}
        '''
        return query

    def _get_nb_entities(self) -> int:
        """Return the number of entities to query.

        Returns:
            int: the number of wikidata entity with the property.

        """
        if self._id_list is not None:
            return len(self._id_list)
        else:
            query = f'''
            SELECT (COUNT(DISTINCT(?entity)) as ?nb_elem)
            WHERE {{
                ?entity wdt:{self._property_wiki} ?value_property .
            }}
            '''

            logger.debug(query)
            logger.info("Querying WikiData to count the number of entities.")

            result_query = self._request_wikidata(query)
            nb_entities_df = self._json_to_pandas(result_query)
            nb_entities = int(nb_entities_df.iloc[0, 0])
            logger.info("{} entities in the property {} have been found."
                        .format(nb_entities, self._property_wiki))
            return nb_entities

    def _query_generator(self):
        """Query_generator.

        Generate all the SPARQL queries needed.

        Yields:
            (pd.DataFrame, bool): the result of the query, flag indicating
                if the next query is for another language or not.

        """
        nb_entities = self._get_nb_entities()
        if self._id_list is not None:
            nb_entity_request = self._nb_elems_values
        else:
            nb_entity_request = self._limit

        nb_queries = math.ceil(nb_entities/nb_entity_request) \
            * len(self._languages_list)

        logger.info('Starting the {} queries.'.format(nb_queries))
        # First loop on the different languages
        for language in self._languages_list:
            logger.info('Starting queries for lang {}'.format(language))
            result_lang_df = pd.DataFrame()

            nb_queries = math.ceil(nb_entities/nb_entity_request)
            # Loop to ensure the limitation of entities number in one query
            for query_iter in tqdm(range(nb_queries)):
                query = self._format_query(language,
                                           query_iter * nb_entity_request)
                result_query = self._request_wikidata(query)
                result_offset_df = \
                    self._json_to_pandas(result_query)
                flag_lang = query_iter + 1 == nb_queries
                yield result_offset_df, flag_lang

    def _get_value(self, dict_data):
        """Extract the value of the dictionaries given by a request.

        Args:
            dict_data (dict): a dictionary extracted from a WikiData query.

        Returns:
            dict: the dictionary, with only the name of the columns and the
                values.

        """
        dict_query = {key: value['value'] for key, value in
                      dict_data.items()}
        return dict_query

    def _json_to_pandas(self, json_text):
        """json_to_pandas.

        Transform the resulting JSON of a response to a WikiData query
        into a DataFrame.

        Args:
            json_text (json): a result from a query to WikiData SPARQL.

        Returns:
            pd.DataFrame: the cleaned results from the query.

        """
        json_text = [self._get_value(elem) for elem
                     in json_text['results']['bindings']]
        logger.debug("Parsing of the query successful.")
        return pd.DataFrame(json_text)

    def translate(self, id_list=None):
        """translate.

        Public call to the class to launch the queries to extract the labels,
        alternative labels and value of a specific property of the requested
        entities.

        Returns:
            pd.DataFrame: containing all the labels and alternative
                labels of the entities with the given property in the
                languages. Columns: ['entity', 'value_property',
                ('labelLang', 'altLang') with Lang in languages_list]

        """
        self._id_list = id_list

        result_df = pd.DataFrame(columns=['entity', 'value_property'])
        result_lang_df = pd.DataFrame(columns=['entity', 'value_property'])
        full_result_df = pd.DataFrame(columns=['entity', 'value_property'])
        for query_df, flag_lang in self._query_generator():
            result_lang_df = pd.concat([result_lang_df, query_df], axis=0,
                                       join='outer', ignore_index=True,
                                       sort=True)
            # If the next query is a different language, merge to full_result
            if flag_lang:
                full_result_df = pd.merge(full_result_df, result_lang_df,
                                          how='outer',
                                          on=['entity', 'value_property'])
                result_lang_df = pd.DataFrame(columns=['entity',
                                                       'value_property'])
        return full_result_df
