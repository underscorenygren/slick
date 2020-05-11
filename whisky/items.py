import json

from scrapy.loader import processors

import lib
from slick import model, item, parser
from whisky import parsers, models


logger = lib.init_logger("whisky.items")


class DistilleryMatcher(object):
	def __init__(self):
		self.parser = None
		try:
			with open('whisky/data/distilleries.txt', 'r') as f:
				self.parser = parsers.make_distillery_parser(f.readlines())
		except IOError:
			pass

	def __call__(self, v):
		if not self.parser:
			return None
		return self.parser(v)


distillery_matcher = DistilleryMatcher()

WhiskyItem = model.realize_item_class('WhiskyItem', models.Whisky)

WhiskySearchResultItem = model.realize_item_class('WhiskySearchResultItem', models.WhiskySearchResult)


def fill_item_from_name(_item):
	"""Fills item data fields from it's name"""
	string = _item.get('name')
	if not string:
		return _item

	for attr_name in ['currency', 'abv',
			'cask_no', 'size', 'vintage', 'age']:
		fn = getattr(parsers, attr_name)
		if _item.get(attr_name) is None:
			_item[attr_name] = fn(string)

	if _item.get('distillery') is None:
		_item['distillery'] = distillery_matcher(string)

	return _item


def grand_whisky_search_result(response):
	prefix = 'window.auction_data'
	xpath = f'//script[contains(., {prefix})]/text()'
	data = None
	for found in response.xpath(xpath):
		gotten = found.get()
		if prefix in gotten:
			data = gotten
			break
	if not data:
		return

	entries = data.split('\n')
	first = entries[1].strip().strip(';')
	obj = first[len(prefix) + len(' = '):]
	loaded = json.loads(obj)
	mapping = [
			('name', 'name', ()),
			('url', 'url', ()),
			('price', 'highest_bid', (parser.read_float,)),
			('currency', 'highest_bid', (parser.read_float,)),
	]

	for entry in loaded:
		loader = item.BaseLoader(item=WhiskySearchResultItem())

		for item_name, lookup, procs in mapping:
			val = entry.get(lookup)
			if val is not None:
				loader.add_value(item_name, val, *procs)

		loader.add_value('domain', entry.get('url'),
			processors.TakeFirst(), lib.get_domain)
		yield loader.load_item()


def grand_whisky_item(response):
	loader = item.BaseLoader(item=WhiskyItem(), response=response)
	loader.add_xpath('name', '//*[@id="content"]/div[1]/div/h1/text()')
	loader.add_css('origin', 'ul.lotProps > li:nth-child(3)::text')
	loader.add_css('size', 'ul.lotProps > li:nth-child(5)::text', parsers.take_first_nonempty(parsers.size))
	loader.add_css('abv', 'ul.lotProps > li:nth-child(7)', parsers.take_first_nonempty(parsers.abv))
	loader.add_css('price', 'div.innerPriceWrap > div > span > span.USD.show')
	return loader.load_item()


class DekantaSearchResultItem(WhiskySearchResultItem):

	@staticmethod
	def load(box):
		loader = item.BaseLoader(item=DekantaSearchResultItem(), selector=box)
		loader.add_css('name', '.product-title a::text')
		loader.add_css('price', '.amount::text')
		loader.add_css('currency', '.woocs_price_code::text',
			processors.TakeFirst(), parsers.currency)
		loader.add_css('currency', '.woocs_price_code ins::text',
			processors.TakeFirst(), parsers.currency)
		loader.add_css('url', '.product-title a::attr(href)')
		loader.add_css('domain', '.product-title a::attr(href)',
			processors.TakeFirst(), lib.get_domain)

		return loader.load_item()

	@staticmethod
	def loads(response):
		for box in response.css('.box-text-products'):
			yield DekantaSearchResultItem.load(box)


class DekantaWhiskyItem(WhiskyItem):

	@staticmethod
	def load(response):
		loader = item.BaseLoader(item=DekantaWhiskyItem(), response=response)
		loader.add_css('name', '.product-title::text')
		loader.add_css('price', '.amount::text')
		loader.add_css('currency', '.woocs_price_code::text',
			processors.TakeFirst(), parsers.currency)
		loader.add_css('currency', '.woocs_price_code ins::text',
			processors.TakeFirst(), parsers.currency)
		loader.add_css('distillery', '.product_distillery::text')
		loader.add_css('origin', '.product_origin::text')
		loader.add_css('age', '.product_years::text',
			processors.TakeFirst(), parser.read_int)
		loader.add_css('abv', '.product_alcohol::text',
			processors.TakeFirst(), parsers.abv)
		loader.add_css('size', '.product_bottlesize::text',
			processors.TakeFirst(), parsers.size)

		return loader.load_item()


class YahooSearchResultItem(WhiskySearchResultItem):
	@staticmethod
	def load(selector):
		loader = item.BaseLoader(item=YahooSearchResultItem(), selector=selector)
		loader.add_css('name', '.Product__title a::text')
		loader.add_css('price', '.Product__priceValue::text')
		loader.add_css('url', '.Product__title a::attr(href)')

		return loader.load_item()
