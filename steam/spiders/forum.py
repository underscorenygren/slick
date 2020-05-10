"""scrapes forum search"""
import random

import scrapy

import env
from slick import spider

from steam import items, spiders


QUERY_URL = f'https://steamcommunity.com/discussions/forum/search/?q={env.forum_search}'


class ForumSpider(spider.DBMixin,
		spider.MetricsMixin,
		spiders.GameDeveloperParsingMixin,
		scrapy.Spider):
	"""scrapes steam forums"""
	name = "forum"
	_item_classes = (
		items.ForumPageItem,
		items.GameItem,
		items.DeveloperItem,
	)

	start_urls = [QUERY_URL]

	def __init__(self):
		"""steam community isn't friendly to scraping, blocks you,
		so we run this spider at a slower rate"""
		super().__init__()
		self.download_delay = 3

	def parse(self, response):
		"""initial parse parses search result, and yields all request for all pages"""
		for item in self.parse_forum_search(response):
			yield item

		links = response.css('.pagelink::attr(href)').getall()
		if links:
			last_link = links[-1]
			_, last_page = last_link.split('&')[-1].split('=')
			urls = []
			for i in range(1, int(last_page)):
				urls.append(f'{QUERY_URL}&p={i}')

			random.shuffle(urls)
			for href in urls:
				yield scrapy.Request(url=href, callback=self.parse_forum_search)

	def parse_forum_search(self, response):
		"""entrypoint for forum parsing"""

		for href in response.css('.forum_topic_overlay::attr(href)').getall():
			yield scrapy.Request(url=href, callback=self.parse_forum_page)

	def parse_forum_page(self, response):
		"""parses forum page"""
		forum_page = items.load_forum_page(response)
		yield forum_page
		developer_url = forum_page.get('developer', {}).get('url')
		# some forums like https://steamcommunity.com/groups/homestream/discussions/0/1608274347738014936
		# aren't game specific
		if developer_url:
			yield scrapy.Request(url=developer_url, callback=self.parse_community_page)

	def parse_community_page(self, response):
		"""parses url from forums, which isnt' steam store"""
		for obj in response.xpath('//*[@id="ModalContentContainer"]/div[1]/div[1]/div[3]/div[2]/a'):
			href = obj.attrib.get('href')
			yield self.game_request(href)
