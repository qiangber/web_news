# -*- coding: utf-8 -*-
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from web_news.items import SpiderItem
from web_news.misc.spiderredis import SpiderRedis


class Jljgdj(SpiderRedis):
    name = "jljgdj"
    website = u"吉林机关党建"
    allowed_domain = "jljgdj.org"
    start_urls = ["http://www.jljgdj.org/"]

    rules = [
        Rule(LinkExtractor(allow=("jljgdj.org/NewsPage",)), callback="get_news", follow=False),
        Rule(
            LinkExtractor(allow=("jljgdj.org/newslist",)), follow=True),
    ]

    def get_news(self, response):
        loader = ItemLoader(item=SpiderItem(), response=response)
        try:
            loader.add_value('title', response.xpath('//p[@class="title1"]/text()').extract_first())

            date = response.xpath('//pre[@class="f_title"]/text()').extract_first()
            loader.replace_value('date', date[date.find(u"日期：")+3:][0:10])

            loader.add_value('content',
                             ''.join(response.xpath('//div[@class="contents"]/descendant-or-self::text()').extract()))

        except Exception as e:
            self.logger.error('error url: %s error msg: %s' % (response.url, e))
            loader.add_value('title', '')
            loader.add_value('date', '1970-01-01')
            loader.add_value('content', '')

        loader.add_value('url', response.url)
        loader.add_value('collection_name', self.name)
        loader.add_value('website', self.website)

        return loader.load_item()
