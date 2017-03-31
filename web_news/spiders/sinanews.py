# -*- coding: utf-8 -*-
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from web_news.items import SpiderItem
from web_news.misc.spiderredis import SpiderRedis


class SinaNews(SpiderRedis):
    name = "sinanews"
    website = u"新浪网"
    allowed_domain = "sina.com.cn"
    start_urls = ["http://www.sina.com.cn/"]

    rules = [
        Rule(LinkExtractor(allow=("news\.sina.*?\d+\.shtml",), deny=("list", "video")), callback="get_news", follow=False),
        Rule(LinkExtractor("news"), follow=True)
    ]

    def get_news(self, response):
        loader = ItemLoader(item=SpiderItem(), response=response)
        try:
            loader.add_value("title", response.xpath('//h1[@id="artibodyTitle"]/text()').extract_first())
            loader.add_value("title", response.xpath('//div[@class="article-header clearfix"]/h1/text()').extract_first())
            loader.add_value("title", response.xpath('//h2[@id="titleText"]/text()').extract_first())
            loader.add_value("title", response.xpath('//h1[@id="main_title"]/text()').extract_first())
            loader.add_value("title", response.xpath('//h1[@id="artibodyTitle"]/text()').extract_first())
            loader.add_value("title", response.xpath('//span[@class="location"]/h1/text()').extract_first())

            url = response.url
            loader.add_value("date", url[url.rfind('/', 0, url.rfind('/')) + 1:url.rfind('/')])

            loader.add_value("content",
                             ''.join(response.xpath('//div[@id="artibody"]//p/descendant-or-self::text()').extract()))
            loader.add_value("content",
                             ''.join(response.xpath('//div[@class="article-body main-body"]//p/descendant-or-self::text()').extract()))
            loader.add_value("content",
                             ''.join(response.xpath('//div[@id="mainContent"]//p/descendant-or-self::text()').extract()))
        except Exception as e:
            self.logger.error('error url: %s error msg: %s' % (response.url, e))
            loader.add_value('title', '')
            loader.add_value('date', '1970-01-01 00:00:00')
            loader.add_value('content', '')

        loader.add_value('url', response.url)
        loader.add_value('collection_name', self.name)
        loader.add_value('website', self.website)

        return loader.load_item()
