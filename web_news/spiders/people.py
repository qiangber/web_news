# -*- coding: utf-8 -*-
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from web_news.items import SpiderItem
from web_news.misc.spiderredis import SpiderRedis


class SinaNews(SpiderRedis):
    name = "people"
    website = u"人民网"
    allowed_domain = "people.com.cn"
    start_urls = ["http://www.people.com.cn/"]

    rules = [
        Rule(LinkExtractor(allow=("(politics|news|world|finance|tw|military|opinion|leader|legal|society|edu|scitech)."
                                  "people.com.cn/n1/")), callback="get_news", follow=False),
        Rule(
            LinkExtractor(allow=("(politics|news|world|finance|tw|military|opinion|leader|legal|society|edu|scitech)."
                                 "people.com.cn/GB/",)), follow=True),
    ]

    def get_news(self, response):
        loader = ItemLoader(item=SpiderItem(), response=response)
        try:
            loader.add_value('title', response.xpath('//div[@class="text"]/h1/text()').extract_first())
            loader.add_value('title', response.xpath('//div[@class="text_c clearfix"]/h1/text()').extract_first())
            loader.add_value('title', response.xpath('//div[@class="text_c"]/h1/text()').extract_first())
            loader.add_value('title', response.xpath('//div[@class="d2_left wb_left fl"]/h1/text()').extract_first())
            loader.add_value('title', response.xpath('//div[@class="clearfix w1000_320 text_title"]/h1/text()').extract_first())

            url = response.url
            url = url[url.find('n1') + 3:url.rfind('/')]
            loader.replace_value('date', url[0:4] + '-' + url[5:7] + '-' + url[7:])

            loader.add_value('content',
                             ''.join(response.xpath('//div[@class="text_c"]/descendant-or-self::text()').extract()))
            loader.add_value('content',
                             ''.join(response.xpath('//div[@class="text_show"]/descendant-or-self::text()').extract()))
            loader.add_value('content',
                             ''.join(response.xpath('//div[@class="show_text"]/descendant-or-self::text()').extract()))
            loader.add_value('content',
                             ''.join(response.xpath('//div[@id="p_content"]/descendant-or-self::text()').extract()))
            loader.add_value('content',
                             ''.join(response.xpath('//div[@id="rwb_zw"]/descendant-or-self::text()').extract()))

        except Exception as e:
            self.logger.error('error url: %s error msg: %s' % (response.url, e))
            loader.add_value('title', '')
            loader.add_value('date', '1970-01-01')
            loader.add_value('content', '')

        loader.add_value('url', response.url)
        loader.add_value('collection_name', self.name)
        loader.add_value('website', self.website)

        return loader.load_item()
