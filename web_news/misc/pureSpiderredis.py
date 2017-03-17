# -*- coding: utf-8 -*-
import time

from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.spiders import CrawlSpider, Spider
from scrapy.http import Request, HtmlResponse
from filter import Filter
from scrapy_redis.connection import get_redis_from_settings
import json

from web_news.misc.LogSpider import LogStatsDIY


class PureSpiderRedis(Spider):
    """
    this class is to clear redis dupefilter key, when exit correctly.
    if the spider exit with two INT singal, you may need to clear the key manually.
    """

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
        spider = super(PureSpiderRedis, cls).from_crawler(crawler, *args, **kwargs)
        spider.filter = Filter.from_crawler(spider.crawler, spider.name)
        spider.compete_key()
        spider.crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        spider.l = LogStatsDIY.from_crawler(crawler)

        return spider

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
        time.sleep(300)
        self.logger.info('restart')
        self.compete_key()
        # start_requests won't be filtered
        for req in self.start_requests():
            self.crawler.engine.crawl(req, spider=self)
        raise DontCloseSpider
