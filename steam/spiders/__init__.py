# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import scrapy
from steam import items


class DeveloperParsingMixin(object):
	"""mixin for generating developer requests and parsing them"""

	def developer_request(self, url):
		return scrapy.Request(url,
				callback=self.parse_developer)

	def parse_developer(self, response):
		"""parse game landing page"""
		yield items.load_developer(response)


class GameDeveloperParsingMixin(DeveloperParsingMixin):
	"""mixin for generating game requests and parsing them"""

	@staticmethod
	def make_game_request(url, callback):
		"""static method for making a game request"""
		return scrapy.Request(
			url=url,
			callback=callback,
			cookies=[
				{"name": key,
					"value": value,
					"domain": "store.steampowered.com",
					"path": "/"} for (key, value) in
				[("birthtime", 376041601), ("lastagecheckage", "1-0-1983")]]
			)

	def game_request(self, url, callback=None):
		"""game request on self"""
		callback = callback or self.parse_game
		return GameDeveloperParsingMixin.make_game_request(url, callback)

	def _parse_game(self, response):
		"""actual parsing of game. in inner function so we
		can distinguish between when we re-try age check or not"""
		game = items.load_game(response)
		yield game
		developer = game.get('developer')
		if developer:
			yield self.developer_request(developer['url'])

	def parse_game(self, response):
		"""parses game and attempt developer parsing if found.

		Sometimes agecheck urls arrive, I think we parse them this way.
		If so, we re-try once to send a request that sends cookies"""

		url = response.url
		self.logger.info(f"parsing game for {url}")
		if response.url.find('agecheck') > -1:
			self.logger.info(f"recrawling {url}")
			yield self.game_request(response.url, callback=self._parse_game)
		else:
			self.logger.info(f"parsing actual games for {url}")
			for item in self._parse_game(response):
				yield item
