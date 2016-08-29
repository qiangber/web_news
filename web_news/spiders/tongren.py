# -*- coding: utf-8 -*-
from urlparse import urljoin

import re
from scrapy import Request
from scrapy.loader import ItemLoader

from web_news.items import FroumItem
from web_news.misc.forum import SpiderForum


class TongrenSpider(SpiderForum):
    name = "tongren"
    allowed_domains = ["www.daguizx.com"]
    website = u'铜仁论坛'
    start_urls = (
        'http://www.daguizx.com/tongren/1',
    )

    custom_settings = {
        # 'REDIRECT_ENABLED':True,
        # 'DOWNLOAD_TIMEOUT':2,
    }

    item_url_temp = 'http://www.daguizx.com/forum.php?mod=viewthread&tid=%(item_no)s&extra=page%%3D&page=%(page_no)s'
    def parse_each_node(self, response):
        tbody_list = response.xpath('//tbody[re:test(@id, "normalthread_\d+")]')
        for i, tbody in enumerate(tbody_list):
            item_no = tbody.xpath('descendant::td[@class="num"]/a/@href').re_first('\d+')
            yield Request(url=self.item_url_temp%{'item_no':item_no, 'page_no':1})

    def parse_each_item(self, response):
        ret = None
        if response.meta.get('iteminfo') == None:
            iteminfo = {}
            iteminfo['url'] = response.url
            iteminfo['view_num'] = response.xpath('//div[@class="hm ptn"]/span[2]/text()').extract_first()
            iteminfo['reply_num'] = response.xpath('//div[@class="hm ptn"]/span[5]/text()').extract_first()
            iteminfo['title'] = response.xpath('//span[@id="thread_subject"]/text()').extract_first()
            iteminfo['content'] = ''.join(response.xpath('//td[re:test(@id, "postmessage_\d+")]')[0].xpath('descendant-or-self::text()').extract())
            iteminfo['collection_name'] = self.name
            iteminfo['website'] = self.website
            iteminfo['date'] = response.xpath('//em[re:test(@id, "authorposton\d+")]')[0].xpath('text()').re_first('\d+-\d+-\d+\W\d+:\d+:\d+') \
                               or response.xpath('//em[re:test(@id, "authorposton\d+")]')[0].xpath('span/@title').re_first('\d+-\d+-\d+\W\d+:\d+:\d+')
            # yield Request(url=response.request.url+'?page=100000000', callback=self.parse_each_item, meta={'iteminfo':iteminfo})
            last_page = 'http://www.daguizx.com/forum.php?mod=viewthread&tid=252414#lastpost'
            url = re.sub('tid=\d+', re.search(r'tid=\d+', response.url).group(), last_page)
            ret = Request(url=url, meta={'iteminfo':iteminfo})
        else:
            iteminfo = response.meta.get('iteminfo')
            iteminfo['last_reply'] = response.xpath('//em[re:test(@id, "authorposton\d+")]')[-1].xpath('text()').re_first('\d+-\d+-\d+\W\d+:\d+:\d+') \
                                     or response.xpath('//em[re:test(@id, "authorposton\d+")]')[-1].xpath('span/@title').re_first('\d+-\d+-\d+\W\d+:\d+:\d+')
            item = ItemLoader(item=FroumItem(), response=response)
            for k, v in iteminfo.items():
                item.add_value(k, v)
            ret = item.load_item()
        return ret

    def next_page(self, response):
        next_pg = response.xpath('//a[@class="nxt"]/@href').extract_first()
        base_url = response.xpath('//base/@href').extract_first()
        return Request(url=urljoin(base_url, next_pg)) if next_pg else None