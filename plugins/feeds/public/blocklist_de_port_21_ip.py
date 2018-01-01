import logging
from datetime import timedelta

from core.observables import Ip
from core.feed import Feed
from core.errors import ObservableValidationError


class BlocklistdePort21IP(Feed):
    default_values = {
        'frequency': timedelta(hours=1),
        'source': 'https://lists.blocklist.de/lists/21.txt',
        'name': 'BlocklistdePort21IP',
        'description': 'Blocklist.de IMAP IP blocklist: IPs performing attacks on port 21 (FTP)'
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
                ip.tag(['blocklist', 'ftp'])
            except ObservableValidationError as e:
                logging.error(e)
        except Exception as e:
            logging.debug(e)
