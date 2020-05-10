import scrapy

from steam.models import UrlCache

from steam.spiders import GameDeveloperParsingMixin

class CachingMiddleware(object):
	"""caches url crawls in db. so can be resumed"""

	def has_db(self, spider):
		return hasattr(spider, 'db')

	def process_spider_input(self, response, spider):
		"""marks response as crawled"""
		if self.has_db(spider):
			UrlCache.resolve(spider, response)

	def process_spider_output(self, response, result, spider):
		"""marks a url as crawled"""

		for i in result:
			if isinstance(i, scrapy.Request) and self.has_db(spider):
				UrlCache.insert(spider, i)
			yield i

	def process_start_requests(self, start_requests, spider):
		"""loads cached requets from db"""
		# Called with the start requests of the spider, and works
		# similarly to the process_spider_output() method, except
		# that it doesn’t have a response associated.

		# Must return only requests (not items).
		for r in start_requests:
				yield r

		if self.has_db(spider):
			for cached in UrlCache.get(spider.db, spider.name):
				callback_name = 'parse' if not cached.callback else cached.callback
				fn = getattr(spider, callback_name)
				if fn:
					# TODO this is a bit ugly, should just pickle whole thing
					if callback_name == 'parse_game':
						yield GameDeveloperParsingMixin.make_game_request(cached.url, fn)
					else:
						yield scrapy.Request(url=cached.url, callback=fn)
				else:
					spider.logger.error(f"{callback_name} not registered on {spider.name}")
