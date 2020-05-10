"""scrapes data from steamcharts"""
import scrapy

from slick import spider

from steam import models, items


STEAM_CHARTS_URL = 'https://steamcharts.com'
LAST_PAGE_NUM = 453


def make_steamcharts_url(suffix):
	"""steamshcarts url from suffix"""
	if suffix[0] == '/':
		suffix = suffix[1:]
	return f"{STEAM_CHARTS_URL}/{suffix}"


def get_start_urls(db):
	"""get urls for games in our db"""
	for (steam_id, ) in db.query(models.Game.steam_id).filter(models.Game.steam_id != None):
		yield f'app/{steam_id}'


class ConcurrentPlayersSpider(spider.DBMixin,
	spider.MetricsMixin,
	scrapy.Spider):
	"""scrapes chart data from steamcharts.com"""

	name = "concurrent_players"
	_item_classes = (items.ConcurrentPlayersItem, )

	def __init__(self, *args, **kwargs):
		"""sets start urls from db"""
		super().__init__(*args, **kwargs)
		#self.download_delay = 2  # not sure this is necessary, but they have blocked other things, and there's no real rush

		self.start_urls = [
			make_steamcharts_url(f'top/p.{i}') for i in range(1, LAST_PAGE_NUM)
		] + [
			make_steamcharts_url(suffix) for suffix in get_start_urls(self.db)
		]

	def parse(self, response):
		"""parses search result"""
		for suffix in items.load_concurrent_player_urls(response):
			yield scrapy.Request(url=make_steamcharts_url(suffix), callback=self.parse_concurrent_players)

	def parse_concurrent_players(self, response):
		"""parses concurrent player data from response"""
		yield items.load_concurrent_players(response)
