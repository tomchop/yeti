import json
import logging
import requests

from core.analytics import OneShotAnalytics
from core.errors import GenericYetiError


class EmailRepAPI(object):
    """Base class for querying the EmailRep API."""

    @staticmethod
    def fetch(observable):

        try:
            r = requests.get("https://emailrep.io/{}".format(observable.value))
            if r.ok:
                return r.json()
            else:
                raise GenericYetiError("{} - {}".format(r.status_code, r.content))
        except Exception as e:
            logging.erro(e)
            raise GenericYetiError("{} - {}".format(r.status_code, r.content))


class EmailRep(EmailRepAPI, OneShotAnalytics):
    default_values = {
        'name': 'EmailRep',
        'description': 'Perform a EmailRep query.',
    }

    ACTS_ON = ['Email']

    @staticmethod
    def analyze(observable, results):
        links = set()
        json_result = EmailRepAPI.fetch(observable)
        results = {}

        json_string = json.dumps(json_result, sort_keys=True, indent=4, separators=(',', ': '))
        results.update(raw=json_string)
        results['source'] = "EmailRep"
        results['raw'] = json_string
        observable.add_context(results)

        return list(links)
