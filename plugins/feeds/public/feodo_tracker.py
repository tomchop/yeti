from datetime import datetime, timedelta
import re
import logging

from bs4 import BeautifulSoup
from core.observables import Ip, Hostname, Hash, Url
from core.feed import Feed
from core.errors import ObservableValidationError
import requests


class FeodoTracker(Feed):
    descriptions = {
        'A':
            "Hosted on compromised webservers running an nginx proxy on port 8080 TCP forwarding all botnet traffic to a tier 2 proxy node. Botnet traffic usually directly hits these hosts on port 8080 TCP without using a domain name.",
        'B':
            "Hosted on servers rented and operated by cybercriminals for the exclusive purpose of hosting a Feodo botnet controller. Usually taking advantage of a domain name within ccTLD .ru. Botnet traffic usually hits these domain names using port 80 TCP.",
        'C':
            "Successor of Feodo, completely different code. Hosted on the same botnet infrastructure as Version A (compromised webservers, nginx on port 8080 TCP or port 7779 TCP, no domain names) but using a different URL structure. This Version is also known as Geodo.",
        'D':
            "Successor of Cridex. This version is also known as Dridex",
        'E':
            "Successor of Geodo / Emotet (Version C) called Heodo. First appeared in March 2017."
    }

    variants = {
        'A': "Feodo",
        'B': "Feodo",
        'C': "Geodo",
        'D': "Dridex",
        'E': "Heodo"
    }

    default_values = {
        "frequency":
            timedelta(hours=1),
        "name":
            "FeodoTracker",
        "source":
            "https://feodotracker.abuse.ch/feodotracker.rss",
        "description":
            "Feodo Tracker RSS Feed. This feed shows the latest twenty Feodo C2 servers which Feodo Tracker has identified.",
    }

    def update(self):
        for item in self.update_xml(
                'item', ["title", "link", "description", "guid"]):
            self.analyze(item)

    def analyze(self, item):
        context = item
        date_string = re.search(
            r"\((?P<datetime>[\d\- :]+)\)", context['title']).group('datetime')
        try:
            context['date_added'] = datetime.strptime(
                date_string, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        g = re.match(
            r'^Host: (?P<host>.+), Version: (?P<version>\w)',
            context['description'])
        g = g.groupdict()
        context['version'] = g['version']
        context['description'] = FeodoTracker.descriptions[g['version']]
        context['subfamily'] = FeodoTracker.variants[g['version']]
        context['source'] = self.name
        del context['title']
        new = None
        variant_tag = FeodoTracker.variants[g['version']].lower()
        try:
            if re.search(r"[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}",
                         g['host']):
                new = Ip.get_or_create(value=g['host'])
            else:
                new = Hostname.get_or_create(value=g['host'])
            new.add_context(context)
            new.add_source("feed")
            new.tag([variant_tag, 'malware', 'crimeware', 'banker', 'c2'])

        except ObservableValidationError as e:
            logging.error(e)

        try:
            url_fedeo = context['guid']
            r = requests.get(url_fedeo)
            if r.status_code == 200:

                html_source = r.text

                soup = BeautifulSoup(html_source, 'html.parser')
                tab = soup.find('table', attrs='sortable')
                results = []

                if tab:
                    all_tr = tab.find_all('tr')

                    for tr in all_tr:
                        all_td = tr.find_all('td')
                        if all_td and len(all_td) == 7:
                            results.append({
                                'timestamp': all_td[0].text,
                                'md5_hash': all_td[1].text,
                                'filesize': all_td[2].text,
                                'VT': all_td[3].text,
                                'Host': all_td[4].text,
                                'Port': all_td[5].text,
                                'SSL Certif or method': all_td[6].text
                            })

                for r in results:
                    new_hash = Hash.get_or_create(value=r['md5_hash'])
                    new_hash.add_context(context)
                    new_hash.add_source('feed')
                    new_hash.tag([
                        variant_tag, 'malware', 'crimeware', 'banker', 'payload'
                    ])
                    new_hash.active_link_to(
                        new, 'c2', self.name, clean_old=False)
                    host = Url.get_or_create(
                        value='https://%s:%s' % (g['host'], r['Port']))
                    host.add_source('feed')
                    host.add_context(context)
                    host.tag(
                        [variant_tag, 'malware', 'crimeware', 'banker', 'c2'])
                    new_hash.active_link_to(
                        host, 'c2', self.name, clean_old=False)

        except ObservableValidationError as e:
            logging.error(e)
