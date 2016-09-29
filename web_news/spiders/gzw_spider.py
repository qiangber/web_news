#!/usr/bin/python
# -*- coding:utf-8 -*-
from scrapy.selector import Selector
from scrapy.spider import Spider
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.http import Request, HtmlResponse
from scrapy.http import Request,FormRequest
import re
from web_news.items import *
from web_news.misc.filter import Filter
from web_news.misc.spiderredis import SpiderRedis

class GzwSpider(SpiderRedis):
    name = 'gzw'
    website = '贵州网'
    download_delay = 0.2
    allowed_domains = ['www.gzw.net',
		       'news.gzw.net',
		       'biz.gzw.net',
		       'money.gzw.net',
		       'qiye.gzw.net',
	 	       '888.gzw.net'
    ]
    start_urls = ['http://www.gzw.net/']

    rules = [
        Rule(LinkExtractor(allow=("shtml")), callback="get_news", follow=True),
        Rule(
            LinkExtractor(allow=("news.gzw.net/",
                                 "biz.gzw.net/biznews/",
                                 "money.gzw.net/",
				 "qiye.gzw.net/",
				 "888.gzw.net/",),deny=("news.gzw.net/sports/","news.gzw.net/ent/")), follow=True),
    ]


    def get_news(self,response):
        l = ItemLoader(item=SpiderItem(),response=response)
        l.add_value('title', response.xpath('//h2[@class="titleH2"]/text()').extract())
        l.add_value('title', response.xpath('//div[@class="Article-Left"]/h3/text()').extract())
        l.add_value('title', response.xpath('//div[@class="tit"]/h1/text()').extract())

        l.add_value('date',response.xpath('//div[@class="from"]/span/text()').extract())
        l.add_value('date',response.xpath('//div[@class="CopyFrom"]/text()').extract())
        l.add_value('date',response.xpath('//div[@class="auther-from"]/text()').extract())
        r1 = r"\d{4}\-\d{1,2}\-\d{1,2}\s\d{2}\:\d{2}\:\d{2}"
        date0 = re.compile(r1)
        date = ''.join(l.get_collected_values('date'))
        date1 = date0.findall(date)
        l.replace_value('date', date1[0])
        l.add_value('content',response.xpath('//div[@class="content"]/p/text()').extract())
        l.add_value('content',response.xpath('//div[@class="content"]/p/font/text()').extract())
        l.add_value('content',response.xpath('//div[@class="content"]/text()').extract())

        l.add_value('url', response.url)
        l.add_value('collection_name', self.name)
        l.add_value('website', self.website)
        return l.load_item()
