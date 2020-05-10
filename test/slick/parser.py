"""tests slick parsers"""

from slick import parser

def test_read_bool():
	"""tests boolean conversion"""
	assert True is parser.read_bool("true")
	assert True is parser.read_bool("1")
	assert True is parser.read_bool("on")
	assert True is parser.read_bool("yes")
	assert False is parser.read_bool("false")
	assert False is parser.read_bool("False")
	assert False is parser.read_bool("0")
	assert False is parser.read_bool("off")
	assert False is parser.read_bool("no")


def test_read_int():
	"""tests int conversion"""
	assert 1 == parser.read_int("1")
	assert 1001 == parser.read_int("1'001")
	assert 1001 == parser.read_int("1,001")
	assert 2001 == parser.read_int("  2'001  ")
	assert 10 == parser.read_int("  some embedded 10 number")
	assert 20 == parser.read_int("20.0")


def test_read_float():
	"""tests float conversion"""
	assert 1.0 == parser.read_float("1.0")
	assert 1.1001 == parser.read_float("1.1001")
	assert 211.1001 == parser.read_float("211.1001")
	assert 1001.101 == parser.read_float("1'001.101")


def test_strip_whitespace():
	"""tests whitespace stripping"""
	assert "a" == parser.strip_whitespace("  a   ")


def test_strip_query_string():
	"""tests stripping of query string"""
	url = "https://url.com"
	url_w_query = f"{url}?query=1"
	assert parser.strip_query_string(url) == url
	assert parser.strip_query_string(url_w_query) == url
