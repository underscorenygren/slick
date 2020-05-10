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


def fill_item_from_name(item):
	"""Fills item data fields from it's name"""
	string = item['name']

	for attr_name in ['currency', 'abv',
			'cask_no', 'size', 'vintage', 'age']:
		fn = getattr(parsers, attr_name)
		if item.get(attr_name) is not None:
			item[attr_name] = fn(string)

	if item.get('distillery') is None:
		item['distillery'] = distillery_matcher(string)

	return item


class GrandWhiskyItem(WhiskyItem):
	@staticmethod
	def loads(response):
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

		entries = data.split(';')
		first = entries[0].strip()
		obj = first[len(prefix) + len(' = '):]
		loaded = json.loads(obj)
		mapping = [
				('name', 'name', ()),
				#('url', 'url', ()),
				('price', 'highest_bid', (parser.read_float,)),
				#('currency', 'highest_bid', (parser.read_float,)),
		]

		for entry in loaded:
			loader = item.BaseLoader(item=GrandWhiskyItem())

			for item_name, lookup, procs in mapping:
				val = entry.get(lookup)
				if val is not None:
					loader.add_value(item_name, val, *procs)

			yield loader.load_item()


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
