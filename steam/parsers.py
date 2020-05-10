import datetime
import re

from slick import parser

def _remove_steam_link_filter(value):
	"""Unwraps external links protected by steams linkguard."""
	_split = value.split('=')
	if len(_split) > 1:
		return _split[-1]
	return None


# read_date fn comes from factory
_read_date = parser.make_date_parser(("%b %d, %Y", "%b %d %Y"))


def _read_release_date(value):
	"""reads the release date as a string"""
	val = _read_date(value)
	if val is None:
		# some are "late 2020" for example
		for match in re.findall(r"\d{4}", value):
			month = 9 if "Late" in value else 3 if "Early" in value else 6
			return datetime.datetime(year=int(match), month=month, day=1)

	return val

def _list_or_string(value, fn):
	"""for when we haven't used MapCompose, we apply fn to value or all values,
	e.g TakeFirst from scrapy"""
	if isinstance(value, str):
		return fn(value)
	for s in value:
		res = fn(s)
		if res is not None:
			return res
	return None


def read_release_date(value):
	"""reads the release date as a string. Works on str and iterables"""
	return _list_or_string(value, _read_release_date)


def remove_steam_link_filter(value):
	"""Unwraps external links protected by steams linkguard."""
	return _list_or_string(value, _remove_steam_link_filter)


def read_url_no_query_string(value):
	"""reads a url and strips out it's query string"""
	return _list_or_string(value, parser.strip_query_string)


def read_without_unicode(value):
	"""reads a value while stripping unicode"""
	return _list_or_string(value, parser.strip_unicode)
