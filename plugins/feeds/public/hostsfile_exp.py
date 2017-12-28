import logging
from datetime import timedelta

from core.observables import Hostname
from core.feed import Feed
from core.errors import ObservableValidationError


class HostsFileEXP(Feed):
    default_values = {
        'frequency': timedelta(hours=4),
        'source': 'https://hosts-file.net/exp.txt',
        'name': 'HostsFileEXP',
        'description': 'Sites engaged in the housing, development or distribution of exploits, including but not limited to exploitation of browser, software (inclusive of website software such as CMS), operating system exploits as well as those engaged in exploits via social engineering.'

    }

    def update(self):
        for line in self.update_lines():
            self.analyze(line)

    def analyze(self, line):
        if line.startswith('#'):
            return

        try:
            line = line.strip()
            parts = line.split()

            hostname = str(parts[1]).strip()
            context = {
                'source': self.name
            }

            try:
                host = Hostname.get_or_create(value=hostname)
                host.add_context(context)
                host.add_source('feed')
                host.tag(['exploit', 'blocklist'])
            except ObservableValidationError as e:
                logging.error(e)
        except Exception as e:
            logging.debug(e)
