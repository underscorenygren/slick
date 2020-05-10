"""parses developer sites for emails"""
import random

import scrapy
from scrapy.linkextractors import LinkExtractor

from slick import model

from steam import models, items
from lib import get_domain


DENY_DOMAINS = ['steampowered.com',
		'valve.com',
		'valvesoftware.com',
		'steamcommunity.com',
		'twitter.com',
		'youtube.com',
		'facebook.com',
		'google.com',
		'forum.rising-world.net',
		'amazon.com']


def get_start_urls(db):
	"""parses sites to start with from developer records"""

	urls = []
	domains = set()

	for row in db.query(models.Developer.website)\
			.filter(models.Developer.website != None):

		website = row.website
		urls.append(website)
		domain = get_domain(website)
		domains.add(domain)
		domains.add(domain.replace("www.", ""))

	return urls, domains


class EmailSpider(scrapy.Spider):
	"""searches our developer domains for emails"""

	name = "email"
	_item_classes = (items.EmailItem, )

	def __init__(self, *args, **kwargs):
		"""conencts to db"""
		super().__init__(*args, **kwargs)
		db = model.SqlSession()

		urls, domains = get_start_urls(db)
		# we shuffle the link order in case we re-run it
		random.shuffle(urls)
		self.start_urls = urls

		self.extractor = LinkExtractor(
			allow_domains=domains,
			deny_domains=DENY_DOMAINS)
		db.close()

	def parse(self, response):
		"""finds emails in a rudimentary but effective way using regular expressions"""
		for link in self.extractor.extract_links(response):
			yield scrapy.Request(url=link.url)

		yield from items.load_emails(response)
