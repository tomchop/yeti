import requests
from datetime import timedelta
import logging

from core.feed import Feed
from core.observables import Ip
from core.errors import ObservableValidationError
from core.config.config import yeti_config


class TorExitNodes(Feed):

    default_values = {
        "frequency": timedelta(hours=1),
        "name": "TorExitNodes",
        "source": "https://www.dan.me.uk/tornodes",
        "description": "Tor exit nodes",
    }

    def update(self):
        feed = requests.get(self.source, proxies=yeti_config.proxy).text

        start = feed.find('<!-- __BEGIN_TOR_NODE_LIST__ //-->') + len('<!-- __BEGIN_TOR_NODE_LIST__ //-->')
        end = feed.find('<!-- __END_TOR_NODE_LIST__ //-->')

        feed = feed[start:end].replace('\n', '').replace('<br />', '\n').replace('&gt;', '>').replace('&lt;', '<').split('\n')

        if len(feed) > 10:
            self.status = "OK"

        for line in feed:
            self.analyze(line)
        return True

    def analyze(self, line):

        fields = line.split('|')

        if len(fields) < 8:
            return

        context = {}
        ip = fields[0]
        context['name'] = fields[1]
        context['router-port'] = fields[2]
        context['directory-port'] = fields[3]
        context['flags'] = fields[4]
        context['version'] = fields[6]
        context['contactinfo'] = fields[7]

        context['description'] = "Tor exit node: %s (%s)" % (context['name'], ip)
        context['source'] = self.name
        try:
            ip = Ip.get_or_create(value=fields[0])
            ip.add_context(context)
            ip.add_source("feed")
            ip.tag(['tor'])
        except ObservableValidationError as e:
            logging.error(e)
