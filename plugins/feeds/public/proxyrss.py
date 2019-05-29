import logging
from lxml import etree
from datetime import timedelta
from StringIO import StringIO

from core.observables import Ip
from core.feed import Feed
from core.errors import ObservableValidationError

from dateutil.tz import gettz
tzinfos = {"EDT": gettz("America/New_York")}


class ProxyRSS(Feed):

    default_values = {
        "frequency": timedelta(minutes=30),
        "name": "ProxyRSS",
        "source": "http://www.proxz.com/proxylists.xml",
        "description": "This feed contains daily list of proxy feeds",
    }

    def update(self):
        r = self._make_request()
        tree = etree.parse(StringIO(r.content))
        root = tree.getroot()
        for item in tree.findall("//item", root.nsmap):
            context = {}
            details_dict = {}
            context["link"] = item.findtext("link", namespaces=root.nsmap)
            for details in item.findall("prx:proxy", root.nsmap):
                for field in ["prx:ip", "prx:port", "prx:type", "prx:country", "prx:check_timestamp"]:
                    details_dict.setdefault(
                        field.replace("prx:", ""),
                        details.findtext(field, namespaces=root.nsmap))

            context['source'] = self.name
            self.analyze(context, details_dict)

    def analyze(self, context, details_dict):
        tags = [details_dict["type"], "proxy"]
        try:
            ip = Ip.get_or_create(value=details_dict['ip'])
            ip.add_context(context)
            ip.tag(tags)
            ip.add_source(self.name)
        except ObservableValidationError as e:
            logging.error(e)
