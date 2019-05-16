import json
from datetime import datetime

import requests

from core.analytics import OneShotAnalytics
from core.config.config import yeti_config
from core.observables import Hostname, Ip, Observable


class CirclPDNSApi(object):
    settings = {
        "circl_username": {
            "name": "Circl.lu username",
            "description": "Username for Circl.lu API."
        },
        "circl_password": {
            "name": "Circl.lu password",
            "description": "Password for Circl.lu API."
        }
    }

    @staticmethod
    def fetch(observable, settings):
        auth = (
            settings["circl_username"],
            settings["circl_password"]
        )
        API_URL = "https://www.circl.lu/pdns/query/"
        headers = {'accept': 'application/json'}
        results = []
        r = requests.get(API_URL + observable.value, auth=auth,
                         headers=headers, proxies=yeti_config.proxy)
        if r.ok:
            for l in filter(None, r.text.split('\n')):
                obj = json.loads(l)
                results.append(obj)

        return results


class CirclPDNSApiQuery(OneShotAnalytics, CirclPDNSApi):
    default_values = {
        "name": "Circl.lu PDNS",
        "group": "PDNS",
        "description": "Perform passive DNS \
        lookups on domain names or ip address."
    }

    ACTS_ON = ["Hostname", "Ip"]

    @staticmethod
    def analyze(observable, results):
        links = set()
        json_result = CirclPDNSApi.fetch(observable, results.settings)
        json_string = json.dumps(
            json_result, sort_keys=True, indent=4, separators=(',', ': '))

        results.update(raw=json_string)
        result = {}
        result['source'] = 'circl_pdns_query'
        result['raw'] = json_string

        if isinstance(observable, Ip):
            for record in json_result:
                new = Observable.add_text(record['rrname'])
                new.add_source('circl_pdns')
                links.update(
                    observable.link_to(
                        new,
                        source='Circl.lu Passive DNS',
                        description='{} record'.format(record['rrtype']),
                        first_seen=datetime.fromtimestamp(
                            record['time_first']),
                        last_seen=datetime.fromtimestamp(record['time_last'])
                    ))

        elif isinstance(observable, Hostname):
            for record in json_result:
                new = Observable.add_text(record["rdata"])
                new.add_source('circl_pdns')
                links.update(
                    observable.link_to(
                        new,
                        source='Circl.lu Passive DNS',
                        description='{} record'.format(record['rrtype']),
                        first_seen=datetime.fromtimestamp(
                            record['time_first']),
                        last_seen=datetime.fromtimestamp(record['time_last'])
                    ))

        observable.add_context(result)
        return list(links)
