"""scrapes steams local coop tag"""
import urllib.parse

import scrapy

from slick import spider
from steam import spiders, items
from lib import href, _getall


STEAM_TAGS = {
	"co-op-tag": "tags=1685",
	"local-multi-player": "tags=7368",
	"local-co-op": "tags=3841",
	"shared-split-screen": "category3=24",
	"4-player-coop": "tags=4840",
	"co-op-num-players": "category3=9'",
}


def urlencoded_title(_item):
	return urllib.parse.quote_plus(_item['name'])


def search_url(_item):
	return f'https://store.steampowered.com/search/?term={urlencoded_title(_item)}'


class TagsSpider(spider.DBMixin,
		spider.MetricsMixin,
		spiders.GameDeveloperParsingMixin,
		scrapy.Spider):
	"""scrapes steam tags"""

	name = "tags"
	_item_classes = (
		items.SteamSearchResultItem,
		items.GameItem,
		items.DeveloperItem,
	)

	start_urls = [f"https://store.steampowered.com/search/?{query}" for query in STEAM_TAGS.values()]

	def parse(self, response):
		"""main parse entrypoint"""
		for item in self.parse_search_results(response):
			yield item

	def parse_search_results(self, response):
		"""parses tag result, from which we parse out game names,
		and crawl further"""

		for _item in items.load_steam_search_result(response, STEAM_TAGS):
			yield _item
			yield scrapy.Request(url=search_url(_item),
				callback=self.parse_search_result_by_name)

		arr = response.css('.search_pagination_right a::attr(href)').getall()
		if arr:
			href = arr[-1]
			if href:
				yield scrapy.Request(url=href, callback=self.parse)

	def parse_search_result_by_name(self, response):
		"""parses search page on specific game name, to then follow
		and parse out game data"""
		for url in href(response, '#search_resultsRows a', fn=_getall):
			yield self.game_request(url)
			# we only care about the first result, which we assume is the game
			break
