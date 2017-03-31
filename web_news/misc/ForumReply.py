# -*- coding: utf-8 -*-
import json
import time

import datetime
from scrapy import Item
from scrapy import Spider
from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy_redis import get_redis_from_settings

from web_news.misc.LogSpider import LogStatsDIY
from web_news.misc.filter import Filter


class FormReplySpider(Spider):

    def compete_key(self):
        self.server = get_redis_from_settings(self.settings)
        self.redis_compete = self.settings.get('REDIS_COMPETE') % {'spider': self.name}
        self.redis_wait = self.settings.get('REDIS_WAIT') % {'spider': self.name}
        self.key = 1
        # self.server.sadd(self.key, fp)
        while self.server.sadd(self.redis_compete, self.key) == 0:
            self.key = self.key + 1
        self.logger.info("get key %s" % self.key)

    @staticmethod
    def close(spider, reason):
        spider.logger.info("all slave spider exit")
        spider.server.delete(spider.redis_compete)
        spider.server.delete(spider.redis_wait)
        spider.server.delete('%(spider)s:dupefilter' % {'spider': spider.name})
        spider.server.delete('%(spider)s:requests' % {'spider': spider.name})

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FormReplySpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.filter = Filter.from_crawler(spider.crawler, spider.name)
        spider.compete_key()
        spider.crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        spider.l = LogStatsDIY.from_crawler(crawler)
        return spider

    def parse(self, response):
        return self._parse_each_node(response=response)

    def in_time_range(self, timestr):
        timestr = "%d-%s" % (time.localtime().tm_year, timestr)
        node_time = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M')
        dis = datetime.datetime.now() - node_time
        return dis.seconds / 3600 < 2

    def _parse_each_node(self, response):
        requests_it = [i.replace(callback=self._parse_each_item)
                       for i in self.parse_each_node(response)
                       if self.in_time_range(i.meta.get('last_reply'))]
        if len(requests_it) == 0:
            return
        np = self.next_page(response)
        requests_it[-1].meta['nextpage'] = np
        for i in requests_it:
            yield i

    def _parse_each_item(self, response):
        it = self.parse_each_item(response)
        if it is None:
            return
        # it may be item or request
        ret = []
        if isinstance(it, Item):
            it = dict(it)
            if it.get('last_reply') and not self.filter.link_lastupdate(it['url'], it['last_reply']):
                last_page = self.last_page(response)
                if last_page:
                    ret.append(last_page.replace(callback=self._parse_each_reply))
                if response.meta.get('nextpage'):
                    np = response.meta.get('nextpage')
                    ret.append(np.replace(callback=self._parse_each_node))
        else:
            if response.meta.get('nextpage'):
                it.meta['nextpage'] = response.meta.get('nextpage')
            it = it.replace(callback=self._parse_each_item)
        ret.append(it)
        return ret

    def _parse_each_reply(self, response):
        it = self.parse_each_reply(response)
        ret = []
        if it:
            pre_page = self.pre_page(response)
            if pre_page:
                ret.append(pre_page.replace(callback=self._parse_each_reply))
        ret.append(it)
        return ret

    def parse_each_node(self, response):
        """
        :param response:
        :return: requests list
        """
        raise NotImplementedError

    def parse_each_item(self, response):
        """
        :param response:
        :return: (item, response) list
        """
        raise NotImplementedError

    def parse_each_reply(self, response):
        """
        :param response:
        :return: (item, response) list
        """
        raise NotImplementedError

    def next_page(self, response):
        """
        :param response:
        :return: request to next page
        """
        raise NotImplementedError

    def last_page(self, response):
        """
        :param response:
        :return: request to last page
        """
        raise NotImplementedError


    def spiderExit(self):
        # before close spider
        self.server.lpush(self.redis_wait, json.dumps(self.key))
        cnt = self.server.scard(self.redis_compete)
        if self.key == 1:
            t = 0
            while t < cnt:
                self.logger.info("wait %s spiders to stop" % (cnt - t))
                self.server.brpop(self.redis_wait, 0)
                t = t + 1
                cnt = self.server.scard(self.redis_compete)
            self.logger.info("all slave spider exit")
            self.server.delete(self.redis_compete)
            self.server.delete(self.redis_wait)
            self.server.delete('%(spider)s:dupefilter' % {'spider': self.name})

            self.server.publish('REDIS_PUBLISH:' + self.name, 'continue')
            self.logger.info('publish to restart')
        else:
            pubsub = self.server.pubsub()
            pubsub.subscribe('REDIS_PUBLISH:' + self.name)
            for item in pubsub.listen():
                if item['data'] == 'continue':
                    break

                    # super(BjnewsSpider, reason).close()

    def spider_idle(self):
        """Schedules a request if available, otherwise waits."""
        # XXX: Handle a sentinel to close the spider.
        # sleep somtime ?
        self.spiderExit()
        self.logger.info('restart')
        self.compete_key()
        # start_requests won't be filtered
        for req in self.start_requests():
            self.crawler.engine.crawl(req, spider=self)
        raise DontCloseSpider