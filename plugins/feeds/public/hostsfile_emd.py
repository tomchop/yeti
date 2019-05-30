from datetime import datetime, timedelta
import logging

from core.observables import Hostname
from core.feed import Feed
from core.errors import ObservableValidationError


class HostsFileEMD(Feed):
    default_values = {
        'frequency': timedelta(hours=4),
        'source': 'https://hosts-file.net/emd.txt',
        'name': 'HostsFileEMD',
        'description': 'Sites engaged in malware distribution.'
    }

    def update(self):
        for line in self.update_lines():
            if line.startswith('#'):
                continue

            self.analyze(line)

    def analyze(self, line):
        line = line.strip()
        parts = line.split()

        hostname = str(parts[1]).strip()
        context = {'source': self.name}

        try:
            host = Hostname.get_or_create(value=hostname)
            host.add_context(context)
            host.add_source(self.name)
            host.tag(['malware', 'blocklist'])
        except ObservableValidationError as e:
            logging.error(e)
