# -*- coding: utf-8 -*-
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from web_news.items import SpiderItem
from web_news.misc.spiderredis import SpiderRedis


class Lndangjian(SpiderRedis):
    name = "lndangjian"
    website = u"辽宁党建网"
    allowed_domain = "lndangjian.org.cn"
    start_urls = ["http://www.lndangjian.org.cn/"]

    rules = [
        Rule(LinkExtractor("messagexq.asp"), callback="get_news", follow=True),
        Rule(LinkExtractor("messageall.asp"), follow=True)
    ]

    def get_news(self, response):
        loader = ItemLoader(item=SpiderItem(), response=response)
        try:
            loader.add_value("title", response.xpath('//td[@style=" padding-bottom:5px; padding-top:5px"]//tr[2]/td/text()').extract_first())
            date = response.xpath('//td[@style=" padding-bottom:5px; padding-top:5px"]//td[@style="font-size:12px"]/text()').extract_first()
            loader.add_value("date", date[5:15])
            loader.add_value("content",
                             ''.join(response.xpath(
                                 '//td[@style=" padding-bottom:5px; padding-top:5px"]//div/descendant-or-self::text()').extract()))
            loader.add_value("content",
                             ''.join(response.xpath(
                                 '//td[@style=" padding-bottom:5px; padding-top:5px"]//p/descendant-or-self::text()').extract()))
        except Exception as e:
            self.logger.error('error url: %s error msg: %s' % (response.url, e))
            loader.add_value('title', '')
            loader.add_value('date', '1970-01-01 00:00:00')
            loader.add_value('content', '')

        loader.add_value('url', response.url)
        loader.add_value('collection_name', self.name)
        loader.add_value('website', self.website)

        return loader.load_item()
