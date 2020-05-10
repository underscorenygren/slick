"""tests steam spiders"""
import logging

import scrapy

from slick import model, parser
import lib

from steam import models, items
from steam.spiders.tags import TagsSpider

from test import fake_response_from_file

from test.steam import fixtures


logger = lib.init_logger(__name__, level=logging.DEBUG)


def assert_game(item, skip_keys=[], **kwargs):
	"""makes sure game is the same. Can overwrite fields using kwargs"""
	for key, _ in dict(fixtures.GAME, **kwargs).items():
		if key not in skip_keys:
			assert item[key] is not None


def test_load_game_item(game_item):
	"""loads game item from a static page"""

	assert_game(game_item, skip_keys=('on_macos', 'on_linux'))
	assert game_item['developer'] is not None


def test_load_developer_item(developer_item):
	"""tests loading of developer from static page"""

	for key, exp in fixtures.DEVELOPER.items():
		assert developer_item[key] is not None


def test_db_obj_from_item(developer_item):
	"""tests loading of db object from an item"""
	obj = model.new_model_from_item(models.Developer, developer_item)
	for key, exp in fixtures.DEVELOPER.items():
		attr = getattr(obj, key)
		assert attr is not None


def test_load_forum_page(forum_page_item):
	"""tests forum page item parsing"""

	assert forum_page_item['url'] == fixtures.FORUM_URL
	dev = forum_page_item['developer']
	assert dev['name'] == 'Gang Beasts'
	assert dev['url'] == 'https://steamcommunity.com/app/285900'


def test_email_extraction(email_page):
	"""tests extraction of emails from page"""
	emails = set([e['email'] for e in items.load_emails(email_page)])
	assert len(emails) == 2
	assert 'info@cellardoorgames.com' in emails
	assert 'ryan.lee@cellardoorgames.com' in emails

	# trims period
	email = "some@email.com"
	period = f"here is an email with period {email}."
	parsed = [e for e in items.parse_emails(period)]
	assert parsed == [email]

	#doesn't allow images and the like
	email = "not an email screenshot@2.png here"
	parsed = [e for e in items.parse_emails(email)]
	assert not parsed


def test_concurrent_players_extraction(concurrent_players_item):
	"""tests extraction of chart item"""
	fixtures.assert_concurrent_players_item(concurrent_players_item)


def test_concurrent_players_search(concurrent_players_search_page):
	"""tests concurrent players search"""

	_items = items.load_concurrent_player_urls(concurrent_players_search_page)

	assert len(_items) == 25
	assert _items[0] == '/app/730'


def xtest_deduplication(deduplicator, developer_item, forum_page_item, game_item, email_item):
	"""tests deduplication of items"""
	for item in [developer_item, forum_page_item, email_item, game_item]:
		klass = item.__class__
		attr = item._dedup_attribute
		assert attr is not None
		pre_insert = deduplicator.check_duplicate(item)
		assert pre_insert is False
		dup = klass(**{attr: item[attr]})
		post_insert = deduplicator.check_duplicate(dup)
		assert post_insert is True


class FakeSpider(scrapy.Spider):
	"""fake spider class, does nothing"""
	name = "fake"

	def __init__(self, db):
		self.db = db

	def parse(self, response):
		pass


def test_url_cache(db, developer_page):
	"""tests that url caching fns work"""
	def do_nothing(s, r):
		pass

	spider = FakeSpider(db)
	# starts off empty
	res = [x for x in models.UrlCache.get(db, spider.name)]
	assert not res

	# one in cache after insert
	models.UrlCache.insert(spider, developer_page)
	res = [x for x in models.UrlCache.get(db, spider.name)]
	assert res

	# none in crawl after resolve
	models.UrlCache.resolve(spider, developer_page)
	res = [x for x in models.UrlCache.get(db, spider.name)]
	assert not res


class SpiderTester(object):
	"""stubs out the processing by running parse, matching responses to stubbed
	out ones, and yielding fake responses."""

	def __init__(self, spider, first_url, responses, raise_on_missing=False):
		self.spider = spider
		self.responses = responses
		if not responses:
			raise Exception("must register at least one response")
		self.items = []
		self.requests = [scrapy.Request(url=first_url, callback=spider.parse)]
		self.raise_on_missing = raise_on_missing

	def _handle_request(self, request):
		request_url = request.url
		response = self.responses.get(request_url)
		if not response:
			if self.raise_on_missing:
				raise Exception(f"no response for {request_url}")
			else:
				return None, None

		return response, request.callback

	def run(self):
		items = []
		while self.requests:
			request = self.requests[0]
			logger.info(f"processing fake request {request}")
			self.requests = self.requests[1:]
			response, fn = self._handle_request(request)
			if fn:
				assert response is not None
				logger.debug(f"processing {response} with {fn}")
				for thing in fn(response):
					logger.debug(f"processing {thing}")
					if isinstance(thing, scrapy.Request):
						self.requests.append(thing)
					elif isinstance(thing, scrapy.Item):
						items.append(thing)
					else:
						raise Exception(f"unrecognized fn response {thing} {thing.__class__}")
			else:
				logger.debug(f"no function registered for {request}")

		return items


def test_tags_spider():
	"""runs a tags crawl with predefined responses"""

	spider = TagsSpider()
	start_url = TagsSpider.start_urls[0]
	game_url = 'https://store.steampowered.com/app/359550/Tom_Clancys_Rainbow_Six_Siege/?snr=1_7_7_151_150_1'
	urls = {
		start_url: "steam_local_coop_tag",
		'https://store.steampowered.com/search/?term=Tom+Clancy%27s+Rainbow+Six%C2%AE+Siege': 'steam_tags_search_result',
		game_url: 'game',
	}
	responses = dict([(url, fake_response_from_file(f"{name}.html", url=url)) for (url, name) in urls.items()])
	tester = SpiderTester(spider, start_url, responses)
	items = tester.run()
	assert items, f"no items from tags"
	the_game_item = items[-1]
	#because steam_id is parsed from url, we change it here
	assert_game(the_game_item,
		steam_id=359550,
		url=parser.strip_query_string(game_url),
		skip_keys=('on_macos', 'on_linux',))
