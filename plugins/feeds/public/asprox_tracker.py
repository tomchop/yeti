import csv
import logging
from dateutil import parser
from datetime import datetime, timedelta

from core.observables import Url
from core.feed import Feed
from core.errors import ObservableValidationError
from core.config.config import yeti_config


class AsproxTracker(Feed):

    default_values = {
        "frequency": timedelta(hours=1),
        "name": "AsproxTracker",
        "source": "http://atrack.h3x.eu/api/asprox_full_csv.php",
        "description": "This feed contains known Asprox C2 servers",
    }

    def update(self):

        since_last_run = datetime.now() - self.frequency

        resp = self._make_request(proxies=yeti_config.proxy)
        if resp.ok:
            reader = csv.reader(resp.content.splitlines(), quotechar="'")
            for line in reader:
                if line[0] == 'Number':
                    continue

                first_seen = parser.parse(line[8])
                if self.last_run is not None:
                    if since_last_run > first_seen:
                        return

                self.analyze(line)

    def analyze(self, line):

        # split the entry into observables
        Number, Status, CC, Host, Port, Protocol, ASN, Last_Updated, First_Seen, Last_Seen, First_Active, Last_Active, SBL, Abuse_Contact, Details = line

        url = "{}://{}".format(Protocol, Host)
        context = {}
        context['status'] = Status
        context['port'] = Port
        context['cc'] = CC
        context['status'] = Status
        context['date_added'] = datetime.strptime(
            First_Seen, "%Y-%m-%d %H:%M:%S")
        context['last_seen'] = datetime.strptime(
            Last_Seen, "%Y-%m-%d %H:%M:%S") if Last_Seen else datetime.utcnow()
        context['sbl'] = SBL
        context['abuse_contact'] = Abuse_Contact
        context['description'] = Details if Details else "N/A"
        context['source'] = self.name
        try:
            url = Url.get_or_create(value=url)
            url.add_context(context)
            url.add_source("feed")
            url.tag(['asprox', 'c2', 'scanner'])
        except ObservableValidationError as e:
            logging.error(e)
