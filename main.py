"""Entrypoint that runs all our crawls"""
import logging
import time

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from lib import init_logger
from steam.spiders.forum import ForumSpider
from steam.spiders.email import EmailSpider
from steam.spiders.tags import TagsSpider
from steam.spiders.concurrent_players import ConcurrentPlayersSpider
# settings must be imported when running from script
# https://github.com/scrapy/scrapy/issues/1904

from whisky.spiders import DekantaSpider, GrandSpider, YahooSpider

from steam import settings


if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser(description="launches our spiders")
	spider_defs = {
			'grand': GrandSpider,
			'yahoo': YahooSpider,
			'dekanta': DekantaSpider,
			'forum': ForumSpider,
			'tags': TagsSpider,
			'email': EmailSpider,
			'concurrent_players': ConcurrentPlayersSpider}

	for name in spider_defs.keys():
		parser.add_argument(f'--{name}', action='store_true', help=f"launches {name} spider")
	parser.add_argument('--debug', action="store_true", help="enables debug logging")
	parser.add_argument('--disable-spiders', action="store_true",
		help="disables all spiders. Useful when we want to run spiders with docker exec")

	args = parser.parse_args()

	level = logging.DEBUG if args.debug else logging.INFO

	logger = init_logger(__name__, level=level)

	crawler_settings = Settings()
	crawler_settings.setmodule(settings)
	process = CrawlerProcess(settings=crawler_settings)
	at_least_one_spider = False

	if args.disable_spiders:
		logger.info("all spiders disabled")
	else:
		for name, klass in spider_defs.items():
			if getattr(args, name):
				logger.info(f"launching {name} spider")
				process.crawl(klass)
				at_least_one_spider = True

	if not at_least_one_spider:
		# we do this to keep a docker container running
		logger.info("no spiders configured")
		try:
			input("No spiders running, type any key to exit.\n")
		except EOFError:
			logger.info("no input registered, sleeping forever")
			while True:
				time.sleep(1)
	else:
		logger.info("starting crawlers")
		process.start()
		process.join()
		logger.info("crawlers finished")
