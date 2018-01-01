from datetime import timedelta
import logging

from core.observables import Ip
from core.feed import Feed
from core.errors import ObservableValidationError


class BlocklistdeStrongIP(Feed):
    default_values = {
        'frequency': timedelta(hours=1),
        'source': 'https://lists.blocklist.de/lists/strongips.txt',
        'name': 'BlocklistdeStrongIP',
        'description': 'Blocklist.de Strong IP Blocklist: All IPs which are older then 2 month and have more then 5.000 attacks.'
    }

    def update(self):
        for line in self.update_lines():
            self.analyze(line)

    def analyze(self, line):
        if line.startswith('#'):
            return

        try:
            parts = line.split()
            ip = str(parts[0])
            context = {
                'source': self.name
            }

            try:
                ip = Ip.get_or_create(value=ip)
                ip.add_context(context)
                ip.add_source('feed')
                ip.tag(['blocklist', 'strong'])
            except ObservableValidationError as e:
                logging.error(e)
        except Exception as e:
            logging.debug(e)
