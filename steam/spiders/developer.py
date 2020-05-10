"""fills in developer data on developers that are missing"""
import urllib

import scrapy

from slick import spider, model

from lib import href, _getall
from steam import spiders, models, items


def get_start_urls(db):
	"""gets searches for developer based on name"""

	for (name,) in db.query(models.Developer.name)\
			.filter(models.Developer.steam_id == None):
		encoded_name = urllib.parse.quote(name)
		yield f"https://store.steampowered.com/search/?developer={encoded_name}"


class DeveloperSpider(spider.DBMixin,
	spider.MetricsMixin,
	spiders.DeveloperParsingMixin,
	scrapy.Spider):
	"""looks for developers in our db with missing data, and attempts to search for them"""

	name = "developer"
	_item_classes = (items.DeveloperItem, )

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		db = model.SqlSession()
		self.start_urls = [u for u in get_start_urls(db)]
		db.close()

	def parse(self, response):
		"""attempts to parse first result into a developer"""
		for url in href(response, '#search_resultsRows a', fn=_getall):
			yield self.developer_request(url)
