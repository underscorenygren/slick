import pytest

from slick import pipeline, model, item
import lib

from steam import items

from test import fake_response_from_file, session_factory
from test.steam import fixtures


session = session_factory('steam',
		model.get_registered_models(),
		logger=lib.init_logger('test.steam.fixtures'))


@pytest.fixture()
def db(session):
	"""connection to fake db"""
	sess = session()
	yield sess
	sess.close()

@pytest.fixture()
def game_item():
	"""game item loaded from html file"""
	return items.load_game(fake_response_from_file('game.html', url=fixtures.GAME_URL))

@pytest.fixture()
def other_game_item():
	"""game item loaded from html file"""
	return items.load_game(fake_response_from_file('other_game.html', url=fixtures.OTHER_GAME_URL))

@pytest.fixture()
def developer_page():
	"""developer page"""
	return fake_response_from_file('developer.html', url=fixtures.DEVELOPER_URL)


@pytest.fixture()
def developer_item(developer_page):
	"""developer item loaded from html file"""
	return items.load_developer(developer_page)


@pytest.fixture()
def unicode_developer_item():
	"""developer item loaded from html file"""
	return items.load_developer(fake_response_from_file('unicode_developer.html', url=fixtures.DEVELOPER_URL))


@pytest.fixture()
def forum_page_item():
	"""developer item loaded from html file"""
	return items.load_forum_page(fake_response_from_file('forum_page.html', url=fixtures.FORUM_URL))


@pytest.fixture()
def email_page():
	"""page with emails on them"""
	return fake_response_from_file('email.html', url='http://cellardoorgames.com/contact/')


@pytest.fixture()
def email_item(developer_item):
	"""email item fixture"""
	loader = item.BaseLoader(items.EmailItem())
	domain = lib.get_domain(developer_item['website'])
	the_email = f"someone@{domain}"
	loader.add_value('domain', domain)
	loader.add_value('email', the_email)
	loader.add_dependent('developer', developer_item)
	return loader.load_item()


@pytest.fixture()
def concurrent_players_page():
	"""concurret players page"""
	return fake_response_from_file('concurrent_players.html', url=f'https://steamcharts.com/app/{fixtures.GAME_STEAM_ID}')


@pytest.fixture()
def concurrent_players_item(concurrent_players_page):
	"""concurrent players item"""
	return items.load_concurrent_players(concurrent_players_page)


@pytest.fixture()
def concurrent_players_search_page():
	"""concurret players page"""
	return fake_response_from_file('steam_charts_top.html', url=f'https://steamcharts.com/top/p.1')


@pytest.fixture()
def deduplicator():
	"""deduplicates items"""
	return pipeline.ItemDeduplicators()


def assert_concurrent_players_item(concurrent_players_item):
	"""asserts concurrent players item. repeated so in separate fn"""
	assert concurrent_players_item is not None
	assert concurrent_players_item.get('steam_id') == fixtures.GAME_STEAM_ID
	assert concurrent_players_item.get('current') == 768
	assert concurrent_players_item.get('daily') == 853
	assert concurrent_players_item.get('monthly') == 975
	assert concurrent_players_item.get('all_time') == 19076
