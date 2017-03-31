# -*- coding: utf-8 -*-
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from web_news.items import SpiderItem
from web_news.misc.spiderredis import SpiderRedis


class Wenming(SpiderRedis):
    name = "wenming"
    website = u"中国文明网"
    allowed_domain = "wenming.cn"
    start_urls = ["http://www.wenming.cn/"]

    rules = [
        Rule(LinkExtractor(allow=("\d+/t\d+_\d+\.shtml",)), callback="get_news", follow=False),
        Rule(
            LinkExtractor(allow=("wenming.cn/syjj/",)), follow=True),
    ]

    def get_news(self, response):
        loader = ItemLoader(item=SpiderItem(), response=response)
        try:
            loader.add_value('title', response.xpath('//div[@id="title_tex"]/text()').extract_first())
            loader.add_value('title', response.xpath('//div[@class="dc-title"]/text()').extract_first())
            loader.add_value('title', response.xpath('//div[@class="xl-tit"]/text()').extract_first())

            url = response.url
            url = url[url.rfind('/')+2:url.rfind('_')]
            loader.replace_value('date', url[0:4] + '-' + url[4:6] + '-' + url[6:8])

            loader.add_value('content',
                             ''.join(response.xpath('//div[@id="tex"]/descendant-or-self::text()').extract()))
            loader.add_value('content',
                             ''.join(response.xpath('//div[@class="tex"]/descendant-or-self::text()').extract()))
            loader.add_value('content',
                             ''.join(response.xpath('//div[@class="dc-text02"]/descendant-or-self::text()').extract()))

        except Exception as e:
            self.logger.error('error url: %s error msg: %s' % (response.url, e))
            loader.add_value('title', '')
            loader.add_value('date', '1970-01-01')
            loader.add_value('content', '')

        loader.add_value('url', response.url)
        loader.add_value('collection_name', self.name)
        loader.add_value('website', self.website)

        return loader.load_item()
