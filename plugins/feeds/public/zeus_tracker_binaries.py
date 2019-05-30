import re
from datetime import timedelta
from datetime import datetime
import logging

from core.feed import Feed
from core.observables import Url
from core.errors import ObservableValidationError


class ZeusTrackerBinaries(Feed):

    default_values = {
        "frequency": timedelta(hours=1),
        "name": "ZeusTrackerBinaries",
        "source": "https://zeustracker.abuse.ch/monitor.php?urlfeed=binaries",
        "description": "This feed shows the latest 50 ZeuS binaries URLs.",
    }

    def update(self):

        since_last_run = datetime.utcnow() - self.frequency

        for item in self.update_xml('item',
                                    ["title", "link", "description", "guid"]):
            url_string = re.search(r"URL: (?P<url>\S+),",
                                   item['description']).group('url')
            url_string = url_string.replace(
                'http://https://', 'https://')  # feed malformed, nasty hack
            context = {}
            date_string = re.search(r"\((?P<date>[0-9\-]+)\)",
                                    item['title']).group('date')
            context['date_added'] = datetime.strptime(date_string, "%Y-%m-%d")

            if self.last_run is not None:
                if since_last_run > context['date_added']:
                    return

            context['status'] = re.search(
                r"status: (?P<status>[^,]+)", item['description']).group('status')
            context['guid'] = item['guid']
            context['source'] = self.name
            try:
                context['md5'] = re.search(
                    r"MD5 hash: (?P<md5>[a-f0-9]+)",
                    item['description']).group('md5')
            except AttributeError:
                pass

            self.analyze(url_string, context)

    def analyze(self, url_string, context):

        try:
            n = Url.get_or_create(value=url_string)
            n.add_context(context)
            n.add_source("feed")
            n.tag(['zeus', 'delivery', 'banker', 'crimeware', 'malware'])
        except ObservableValidationError as e:
            logging.error(e)
