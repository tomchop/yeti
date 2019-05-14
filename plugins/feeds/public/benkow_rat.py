import requests
from datetime import datetime, timedelta
import csv
import logging

from core.observables import Url, Ip
from core.feed import Feed
from core.errors import ObservableValidationError
from core.config.config import yeti_config

class BenkowTrackerRat(Feed):

    default_values = {
        "frequency": timedelta(hours=12),
        "name": "BenkowTrackerRat",
        "source" : "http://benkow.cc/export_rat.php",
        "description": "This feed contains known Malware C2 servers",
    }

    def update(self):
        resp = requests.get(self.source, proxies=yeti_config.proxy)
        if resp.ok:
            reader = csv.reader(resp.content.strip().splitlines(), delimiter=';', quotechar='"')
            for line in reader:
                self.analyze(line)

    def analyze(self, line):
        if line[0] == 'id':
            return

        ID, Family, _Url, _IP, First_Seen , _blank = line
        if "://" not in _Url:
            _Url = "http://"+_Url

        context = {}
        context['date_added'] = First_Seen
        context['source'] = self.name

        tags = []
        tags.append(Family.lower())
        tags.append("rat")

        try:
            if  _Url:
                url = Url.get_or_create(value=_Url)
                url.add_context(context)
                url.add_source(self.name)
                url.tag(tags)

        except ObservableValidationError as e:
            logging.error(e)

        try:
            if _IP:
                ip = Ip.get_or_create(value=_IP)
                ip.add_context(context)
                ip.add_source(self.name)
                ip.tag(tags)

        except ObservableValidationError as e:
            logging.error(e)
