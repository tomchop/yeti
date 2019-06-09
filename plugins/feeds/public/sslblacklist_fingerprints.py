
import logging
from dateutil import parser
from datetime import timedelta, datetime

from core.feed import Feed
from core.observables import Ip, Hash
from core.errors import ObservableValidationError

TYPE_DICT = {
    "MITM": ['mitm'],
    "C&C": ["c2"],
    "distribution": ["payload_delivery"],
    "sinkhole": ["sinkhole"],
}

class SSLBlackListCerts(Feed):

    default_values = {
        "frequency": timedelta(hours=24),
        "name": "SSLBlackListCerts",
        "source": "https://sslbl.abuse.ch/blacklist/sslblacklist.csv",
        "description":
            "SSLBL SSL Certificate Blacklist (SHA1 Fingerprints)",
    }

    def update(self):

        since_last_run = datetime.now() - self.frequency

        for line in self.update_csv(delimiter=',', quotechar='"'):
            if not line or line[0].startswith("#"):
                continue

            date, sha1, reason = tuple(line)
            first_seen = parser.parse(date)

            if self.last_run is not None:
                if since_last_run > first_seen:
                    return

            self.analyze(line, first_seen, sha1, reason)

    def analyze(self, line, first_seen, sha1, reason):

        tags = []
        tag = reason.split(" ")
        if len(tag) >= 2:
            family = tag[0]
            tags.append(family.lower())
        _type = tag[-1]

        if TYPE_DICT.get(_type):
            tags += TYPE_DICT[_type]

        tags.append("ssl_fingerprint")

        context_hash = {
            'source': self.name,
            'first_seen': first_seen
        }

        try:
            sha1 = Hash.get_or_create(value=sha1)
            sha1.tag(tags)
            sha1.add_context(context_hash)
        except ObservableValidationError as e:
            logging.error("Invalid line: {}\nLine: {}".format(e, line))
