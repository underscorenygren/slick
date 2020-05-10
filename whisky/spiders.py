import scrapy

from slick import spider
from whisky import items
from lib import init_logger


logger = init_logger(__name__)


class GrandSpider(spider.DBMixin, scrapy.Spider):

	name = "grand"
	_item_classes = [
			items.GrandWhiskyItem,
	]

	start_urls = [
		'https://www.thegrandwhiskyauction.com/april-2020',
		'https://www.thegrandwhiskyauction.com/february-2020',
		'https://www.thegrandwhiskyauction.com/january-2020',
	]

	def parse(self, response):
		yield from items.GrandWhiskyItem.load(response)


class DekantaSpider(spider.DBMixin, scrapy.Spider):

	name = "dekanta"
	_item_classes = [
			items.DekantaSearchResultItem,
			items.DekantaWhiskyItem,
	]

	# Todo 1 through 58
	start_urls = [
		'https://dekanta.com/store/?orderby=date',
	] + [
		f'https://dekanta.com/store/page/{page}?orderby=date' for page in range(2, 10)]

	def parse(self, response):
		for item in items.DekantaSearchResultItem.loads(response):
			yield item
			yield scrapy.Request(url=item['url'], callback=self.parse_whisky)

	def parse_whisky(self, response):
		yield items.DekantaWhiskyItem.load(response)


class YahooSpider(spider.DBMixin, scrapy.Spider):
	name = "yahoo"

	_item_classes = [
		items.YahooSearchResultItem,
	]

	start_urls = [
			"https://auctions.yahoo.co.jp/search/search?p=whisky"
	]

	def parse(self, response):
		for product in response.css('.Product'):
			yield items.YahooSearchResultItem.load(product)
