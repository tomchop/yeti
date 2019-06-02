import logging
from dateutil import parser
from datetime import timedelta, datetime

from core.feed import Feed
from core.observables import Url, Ip
from core.errors import ObservableValidationError

class SSLBlackListIP(Feed):

    default_values = {
        "frequency": timedelta(minutes=1440),
        "name": "SSLBlackListIPs",
        "source": "https://sslbl.abuse.ch/blacklist/sslipblacklist.csv",
        "description": "abuse.ch SSLBL Botnet C2 IP Blacklist (CSV)",
    }

    def update(self):

        since_last_run = datetime.now() - self.frequency

        for line in self.update_csv(delimiter=',', quotechar='"'):
            if not line or line[0].startswith("#"):
                continue

            #Firstseen,DstIP,DstPort
            date, dst_ip, port = tuple(line)
            first_seen = parser.parse(date)
            if self.last_run is not None:
                if since_last_run > first_seen:
                    return

            self.analyze(line, first_seen, dst_ip, port)

    def analyze(self, line, first_seen, dst_ip, port):

        tags = []
        tags.append("potentially_malicious_infrastructure")
        tags.append("c2")

        context = dict(source=self.name)
        context["first_seen"] = first_seen

        try:
            ip = Ip.get_or_create(value=dst_ip)
            ip.add_source(self.name)
            ip.tag(tags)
            ip.add_context(context)
        except ObservableValidationError as e:
            logging.error(e)
            return False

        try:
            _url = "https://{dst_ip}:{port}/".format(dst_ip = dst_ip, port=port)
            url = Url.get_or_create(value=_url)
            url.add_source(self.name)
            url.tag(tags)
            url.add_context(context)
        except ObservableValidationError as e:
            logging.error(e)
            return False