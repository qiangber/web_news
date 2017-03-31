# -*- coding: utf-8 -*-
import re
from urlparse import urljoin
from scrapy import Request
from scrapy.loader import ItemLoader

from web_news.items import FroumItem, FroumReplyItem
from web_news.misc.ForumReply import FormReplySpider


class TianyaSpider(FormReplySpider):
    name = "tianya_free"
    allowed_domains = ["bbs.tianya.cn"]
    website = u'天涯论坛-天涯杂谈'
    start_urls = (
        'http://bbs.tianya.cn/m/list-free-1.shtml',
    )

    def parse_each_node(self, response):
        base_url = 'http://bbs.tianya.cn'
        posts = [Request(url=base_url + s.xpath('@href').extract_first(),
                         meta={'last_reply': s.xpath('.//div[@class="time"]/span[2]/text()').extract_first()})
                 for s in response.xpath('//ul[@class="post-list"]/li/a[re:test(@href, "post")]')]
        return posts

    def parse_each_item(self, response):
        # self.logger.debug(response.url)
        iteminfo = {}
        iteminfo['url'] = response.url
        iteminfo['view_num'] = response.xpath('//i[@class="iconfont icon-view"]/text()').extract_first().strip()
        iteminfo['reply_num'] = response.xpath('//i[@class="iconfont icon-reply"]/text()').extract_first().strip()
        iteminfo['title'] = response.xpath('//h1/text()').extract_first()
        try:
            iteminfo['content'] = ''.join(
                response.xpath('//div[@class="bd"]')[0].xpath('descendant-or-self::text()').extract())
        except Exception as e:
            self.logger.debug('ERORR: %s in %s' % (e, response.url))
            iteminfo['content'] = ''
        iteminfo['collection_name'] = self.name
        iteminfo['website'] = self.website
        iteminfo['last_reply'] = response.meta.get('last_reply')
        iteminfo['date'] = response.xpath('//p[@class="time fc-gray"]/text()')[0].extract()
        key = re.findall('-\d+-', response.url)[0]
        iteminfo['key'] = '%s-%s' % (self.name, key[1:-1])
        l = ItemLoader(item=FroumItem(), response=response)
        for k in iteminfo.keys():
            l.add_value(k, iteminfo[k])
        return l.load_item()

    def parse_each_reply(self, response):
        selectors = [sel for sel in response.xpath('//div[starts-with(@class, "item item-ht")]')]
        iteminfo = {}
        sel = selectors[-1]
        if sel:
            replyid = sel.xpath("@data-replyid").extract_first()
            url = response.url
            if self.filter.haveseen_replylink(url, replyid):
                self.logger.info("%s is duplicated!" % url)
                return None
            iteminfo['replyid'] = replyid
            iteminfo['url'] = url
            key = re.findall('-\d+-', response.url)[0]
            iteminfo['key'] = '%s-%s' % (self.name, key[1:-1])
            iteminfo['date'] = sel.xpath('.//p[@class="time fc-gray"]/text()')[0].extract()
        content = []
        for sel in selectors[::-1]:
            try:
                c = ''.join(
                    [p.strip() for p in sel.xpath('div[@class="bd"]')[0].xpath('descendant-or-self::text()').extract()])
                if len(c) < 15:
                    continue
                content.append(c)
            except Exception as e:
                self.logger.debug('ERORR: %s in %s' % (e, response.url))
                continue
        iteminfo['content'] = '=_='.join(content)
        iteminfo['collection_name'] = 'reply'
        iteminfo['website'] = self.website
        l = ItemLoader(item=FroumReplyItem(), response=response)
        for k in iteminfo.keys():
            l.add_value(k, iteminfo[k])
        return l.load_item()

    def next_page(self, response):
        next_pg = response.xpath('//a[@class="u-btn next-btn"]/@href').re_first('/m/list\.jsp\?item=free\&nextid=\d+')
        base_url = 'http://bbs.tianya.cn'
        return Request(url=urljoin(base_url, next_pg)) if next_pg else None

    def pre_page(self, response):
        pre_pg = response.xpath('//a[@class="u-btn pre-btn"]/@href').extract_first()
        base_url = 'http://bbs.tianya.cn'
        return Request(url=urljoin(base_url, pre_pg)) if pre_pg else None

    def last_page(self, response):
        last_pg = response.xpath('//a[@class="u-btn last-btn"]/@href').extract_first()
        base_url = 'http://bbs.tianya.cn'
        return Request(url=urljoin(base_url, last_pg)) if last_pg else None
