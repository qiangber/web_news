# -*- coding: utf-8 -*-
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from web_news.items import SpiderItem
from web_news.misc.spiderredis import SpiderRedis


class Sxdygbjy(SpiderRedis):
    name = "sxdygbjy"
    website = u"山西党建网"
    allowed_domain = "sxdygbjy.com"
    start_urls = ["http://www.sxdygbjy.com/"]

    rules = [
        Rule(LinkExtractor(allow=("sxdygbjy.com/.*?/\d+\.html",)), callback="get_news", follow=False),
        Rule(
            LinkExtractor(allow=("sxdygbjy.com/(xwjj|zdgz|jcdj|dxscg|dkjx|hetk)/",)), follow=True),
    ]

    def get_news(self, response):
        loader = ItemLoader(item=SpiderItem(), response=response)
        try:
            loader.add_value('title', response.xpath('//div[@class="body"]/h1/text()').extract_first())

            date = response.xpath('//div[@class="body"]/h2/text()').extract_first()
            loader.replace_value('date', date[date.find(u'发表时间：')+5:][0:10])

            loader.add_value('content',
                             ''.join(response.xpath('//div[@id="fontinfo"]/descendant-or-self::text()').extract()))

        except Exception as e:
            self.logger.error('error url: %s error msg: %s' % (response.url, e))
            loader.add_value('title', '')
            loader.add_value('date', '1970-01-01')
            loader.add_value('content', '')

        loader.add_value('url', response.url)
        loader.add_value('collection_name', self.name)
        loader.add_value('website', self.website)

        return loader.load_item()
