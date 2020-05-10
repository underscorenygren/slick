"""scrapy definied items"""
# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import re
import urllib

from scrapy.linkextractors import IGNORED_EXTENSIONS

from slick import \
		item, \
		model,  \
		parser
from steam import models, parsers
from lib import txt, get_domain


EMAIL_REGEX = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.([a-zA-Z0-9-.]+))"


SteamSearchResultItem = model.realize_item_class("SteamSearchResultItem", models.SteamSearchResult)

DeveloperItem = model.realize_item_class("DeveloperItem", models.Developer)

GameItem = model.realize_item_class("GameItem", models.Game)

ForumPageItem = model.realize_item_class("ForumPageItem", models.ForumPage)

EmailItem = model.realize_item_class("EmailItem", models.Email)

ConcurrentPlayersItem = model.realize_item_class("ConcurrentPlayersItem", models.ConcurrentPlayers)

# Loaders

def load_developer(response):
	l = item.BaseLoader(DeveloperItem(), response=response)
	url = parser.strip_query_string(response.url)
	l.add_css('name', '.curator_name a::text')
	l.add_css('description', '.page_desc p::text')
	l.add_value('steam_id', url, re=r"/(\w+)$")
	l.add_css('website', 'a.curator_url::attr(href)', parsers.remove_steam_link_filter)
	l.add_value('steam_url', url, parser.strip_query_string)
	l.add_xpath('facebook_followers', '//*[@id="header_curator_details"]/div[1]/span[1]/a/span')
	l.add_xpath('twitch_followers', '//*[@id="header_curator_details"]/div[1]/span[2]/a/span')
	l.add_xpath('twitter_followers', '//*[@id="header_curator_details"]/div[1]/span[3]/a/span')
	l.add_xpath('youtube_followers', '//*[@id="header_curator_details"]/div[1]/span[4]/a/span')
	l.add_css('steam_followers', '.num_followers::text')

	return l.load_item()


def load_developer_from_game_section(response):
	"""Parse developer out from a sub-section in game
	based on content of a column. Making an xpath for that
	is hard, so we just look up the title in code
	using two iterations."""

	def _inner_load(selector):
		loader = item.BaseLoader(DeveloperItem(), selector=selector)
		loader.add_css('name', 'a::text')
		loader.add_css('url', 'a::attr(href)')
		return loader.load_item()

	developer = None
	for dev in response.css('.dev_row'):
		subtitle = txt(dev, '.subtitle')
		if subtitle == 'Developer:':
			developer = _inner_load(dev.css('.summary'))
			break

	return developer


def load_game(response):
	"""loads a game, and potentially it's dependent developer"""
	loader = item.BaseLoader(GameItem(), response=response)

	loader.add_value('steam_id', response.url, re=r"app/(\d+)/")
	loader.add_value('url', response.url, parsers.read_url_no_query_string)
	loader.add_css('name', 'div.apphub_AppName::text')
	loader.add_css('release_date', '.release_date .date::text', parsers.read_release_date)

	# looks for platforms in purchase pane
	for (platform, css_class) in [('windows', 'win'),
			('macos', 'mac'), ('linux', 'linux')]:
		loader.add_css(f'on_{platform}', f'.game_area_purchase_platform .{css_class}')

	loader.add_dependent('developer', load_developer_from_game_section(response))

	return loader.load_item()


def load_forum_page(response):
	forum_page_loader = item.BaseLoader(ForumPageItem(), response=response)

	def _load_developer(response):
		xpath = '//*[@id="AppHubContent"]/div/div[1]/div[1]/div/a[1]'
		developer_loader = item.BaseLoader(DeveloperItem(), response=response)
		developer_loader.add_xpath('name', xpath, re=r'>(.*)<')
		developer_loader.add_xpath('url', xpath, re=r'href="([^"]*)"')

		return developer_loader.load_item()

	def _load_game(response):
		game_loader = item.BaseLoader(GameItem(), response=response)
		game_loader.add_xpath('name', '//*[@id="AppHubContent"]/div/div[1]/div[1]/div/a[1]')
		return game_loader.load_item()

	forum_page_loader.add_value('url', response.url, parser.strip_query_string)
	forum_page_loader.add_dependent('developer', _load_developer(response))
	forum_page_loader.add_dependent('game', _load_game(response))

	return forum_page_loader.load_item()


def load_steam_search_result(response, tags):

	def _response_to_tag():
		"""matches a response to the tag it came from"""
		url = response.url
		parsed = urllib.parse.urlparse(url)
		_tags = parsed.query.split("&")
		for steam_tag_name, steam_tag in tags.items():
			for parsed_tag in _tags:
				if steam_tag == parsed_tag:
					return steam_tag_name, steam_tag
		return None, None

	def _load_game(name):
		game_loader = item.BaseLoader(GameItem())
		game_loader.add_value('name', name)
		return game_loader.load_item()

	tag_name, tag_value = _response_to_tag()

	if not tag_name:
		return

	for _txt in response.css('.title::text').getall():
		result_loader = item.BaseLoader(SteamSearchResultItem())
		result_loader.add_value('tag_name', tag_name)
		result_loader.add_value('tag_value', tag_value)
		result_loader.add_value('name', _txt)
		game = _load_game(_txt)
		result_loader.add_dependent('game', game)
		yield result_loader.load_item()


def parse_emails(txt):
	for m in re.finditer(EMAIL_REGEX, txt):
		g = m.groups()
		email = g[0]
		suffix = g[1]
		if suffix not in IGNORED_EXTENSIONS:
			yield email.strip('.')


def load_emails(response):
	for email in parse_emails(response.body.decode('utf8', 'ignore')):
		url = response.url
		yield EmailItem(email=email, domain=get_domain(url), url=url)


def load_concurrent_players(response):
	def _load_game():
		game_loader = item.BaseLoader(GameItem(), response=response)
		game_loader.add_xpath('name', '//*[@id="app-title"]/a/text()', parsers.read_without_unicode)
		return game_loader.load_item()

	loader = item.BaseLoader(ConcurrentPlayersItem(), response=response)
	loader.add_value('steam_id', response.url, re=r"/(\w+)$")
	loader.add_xpath('current', '//*[@id="app-heading"]/div[1]/span')
	loader.add_xpath('daily', '//*[@id="app-heading"]/div[2]/span')
	loader.add_xpath('all_time', '//*[@id="app-heading"]/div[3]/span')
	loader.add_xpath('monthly', '//*[@id="content-wrapper"]/div[6]/table/tbody/tr[1]/td[2]')

	loader.add_dependent('game', _load_game())

	return loader.load_item()


def load_concurrent_player_urls(response):
	urls = response.xpath('//*[@class="game-name left"]/a/@href').getall()
	return [str(i) for i in urls]
