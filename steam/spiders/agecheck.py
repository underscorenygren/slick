"""tests breaking agecheck on steam"""
from steam.spiders import GameDeveloperParsingMixin
import scrapy


class AgecheckSpider(scrapy.Spider, GameDeveloperParsingMixin):
	"""Attempts to route arounds age check."""
	name = "agecheck"

	def start_requests(self):
		url = 'https://store.steampowered.com/agecheck/app/261640/?snr=2_9_100000_'
		url = 'https://store.steampowered.com/app/359550?snr=2_9_100000_'
		yield self.game_request(url)
