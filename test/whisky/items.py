import pytest

import test

import lib
from whisky import items


DEKANTA_SEARCH_URL = 'https://dekanta.com/store/'
DEKANTA_ITEM_URL = 'https://dekanta.com/store/yamazaki-12-year-old-single-malt-final-version/'
GRAND_SEARCH_URL = 'https://www.thegrandwhiskyauction.com/april-2020'
GRAND_ITEM_URL = 'https://www.thegrandwhiskyauction.com/lot-130107/macallan-easter-elchies-black-2019/auction-16'


@pytest.fixture()
def dekanta_search_response():
	"""dekanta search result from file"""
	return test.fake_response_from_file('dekanta_search.html', url=DEKANTA_SEARCH_URL)


@pytest.fixture()
def dekanta_item_response():
	"""dekanta search result from file"""
	return test.fake_response_from_file('dekanta_item.html', url=DEKANTA_ITEM_URL)


@pytest.fixture()
def grand_search_response():
	"""dekanta search result from file"""
	return test.fake_response_from_file('grand_search.html', url=GRAND_SEARCH_URL)

@pytest.fixture()
def grand_item_response():
	"""dekanta search result from file"""
	return test.fake_response_from_file('grand_item.html', url=GRAND_ITEM_URL)


def test_dekanta_search(dekanta_search_response):

	len_ref = 9 * 4  # 36
	_items = [i for i in items.DekantaSearchResultItem.loads(dekanta_search_response)]
	assert len_ref == len(_items)

	_item = _items[0]
	assert _item['name'] is not None
	assert _item['price'] is not None
	assert _item['currency'] is not None
	assert _item['url'] is not None
	assert _item['domain'] == lib.get_domain(_item['url'])


def test_dekanta_item(dekanta_item_response):

	_item = items.DekantaWhiskyItem.load(dekanta_item_response)

	name_ref = 'Suntory Yamazaki 12 Year Old Single Malt Final Version'
	price_ref = 299.99
	currency_ref = 'USD'
	origin_ref = 'Japanese'
	age_ref = 12
	abv_ref = 43.0
	distillery_ref = 'Yamazaki'
	size_ref = 700

	assert name_ref == _item['name']
	assert price_ref == _item['price']
	assert currency_ref == _item['currency']
	assert origin_ref == _item['origin']
	assert age_ref == _item['age']
	assert abv_ref == _item['abv']
	assert distillery_ref == _item['distillery']
	assert size_ref == _item['size']


def test_grand_search(grand_search_response):

	len_ref = 36
	_items = [i for i in items.grand_whisky_search_result(grand_search_response)]
	assert len_ref == len(_items)

	name_ref = 'Macallan - Exceptional Single Cask 2019/ESH / 14812/01'
	price_ref = 2950.0

	_item = _items[0]
	assert name_ref == _item['name']
	assert price_ref == _item['price']


def test_grand_item(grand_item_response):
	_item = items.grand_whisky_item(grand_item_response)
	name_ref = "Macallan - Easter Elchies Black - 2019"
	origin_ref = "Scotland"
	size_ref = 700
	abv_ref = 49.7
	assert name_ref == _item['name']
	assert origin_ref == _item['origin']
	assert size_ref == _item['size']
	assert abv_ref == _item['abv']
