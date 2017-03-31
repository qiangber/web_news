# -*- coding: utf-8 -*-
from pymongo import MongoClient
from scrapy.http import HtmlResponse


class Filter(object):

    def __init__(self, client, db, col, name):
        self.client = client
        self.db = db
        self.col = col
        self.seen = set()
        self.name = name

    def _requests_to_follow(self, response, _rules):
        if not isinstance(response, HtmlResponse) or len(_rules) == 0:
            return []
        if _rules[0].process_links:
            return _rules[0].process_links((lnk for lnk in _rules[0].link_extractor.extract_links(response)))
        else:
            return (lnk for lnk in _rules[0].link_extractor.extract_links(response))

    def haveseenlink(self, link):
        if link in self.seen:
            return True
        ret = self.col.find({'url': link, 'collection_name': self.name}).count() > 0
        
        if ret:
            self.seen.add(link)

        return ret

    def haveseen_replylink(self, link, replyid):
        if link+replyid in self.seen:
            return True
        ret = self.db['reply'].find({'url': link, 'collection_name': 'reply', 'replyid': replyid}).count() > 0

        if ret:
            self.seen.add(link+replyid)

        return ret

    def link_lastupdate(self, link, last_reply):
        if link + last_reply in self.seen:
            return True
        ret = self.col.find({'url': link, 'collection_name': self.name, 'last_reply': last_reply}).count() > 0

        if ret:
            self.seen.add(link+last_reply)
        return ret

    def bool_fllow(self, response, _rules):
        links = list(self._requests_to_follow(response, _rules))
        _links = []
        for link in links:
            if not self.haveseenlink(link.url):
                _links.append(link)
        return _links

    def url_exist(self, url):
        flag = self.col.find({'url': url, 'collection_name': self.name}).count() > 0
        return flag

    @classmethod
    def from_crawler(cls, crawler, name):
        mongo_db = crawler.settings.get('MONGO_DATABASE')
        mongo_collection = crawler.settings.get('MONGO_COLLECTION')
        mongo_username = crawler.settings.get('MONGO_USER')
        mongo_password = crawler.settings.get('MONGO_PASSWORD')
        mongo_ip = crawler.settings.get('MONGO_IP')
        mongo_port = crawler.settings.get('MONGO_PORT')
        client = MongoClient(mongo_ip, mongo_port)
        db = client[mongo_db]
        db.authenticate(mongo_username, mongo_password)
        col = db[mongo_collection]
        return cls(client=client, db=db, col=col, name=name)

    def close(self):
        self.client.close()