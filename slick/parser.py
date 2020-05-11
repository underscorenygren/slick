import datetime
import re

from w3lib import html

# Value Parsers

def read_bool(value):
	"""converts a value to boolean"""
	if hasattr(value, 'lower'):
		if value.lower() in ['false', 'no', '0', 'off']:
			return False
	return bool(value)


def _strip_number(value):
	repls = ('"', "'", "\n", ',')
	for rep in repls:
		value = value.replace(rep, '')
	return strip_whitespace(value)


def read_int(value):
	"""reads string value as int. Handles , separators for large number and rounds floats with ."""
	if not isinstance(value, str):
		return value
	if not value:
		return 0

	stripped = _strip_number(value)
	reg = re.search(r'[.\d]+', stripped)
	result = reg[0] if reg else stripped

	if (result.find('.') != -1):
		return int(round(float(result)))
	return int(result)


def read_float(value):
	"""reads string value as float. Handles , separators for large numbers"""
	if not isinstance(value, str):
		return value
	if not value:
		return 0.0
	stripped = _strip_number(value)
	return float(stripped)


def read_string(value):
	return str(value)


# Cleaners


def strip_whitespace(value):
	"""removes whitespace"""
	if hasattr(value, 'strip'):
		return value.strip()
	return value


def strip_query_string(value):
	"""strings query string from url"""
	if isinstance(value, str):
		return value.split('?')[0]
	return value


def strip_tags(value):
	"""removes tags"""
	if isinstance(value, str):
		return html.remove_tags(value)
	return value


def strip_unicode(value):
	if hasattr(value, 'encode'):
		return value.encode('ascii', 'ignore').decode()
	return value

# Value Parser Factories

def make_date_parser(format_strings):
	"""makes a date parser that tries many date format strings"""
	def parser(value):
		for fmt_str in format_strings:
			try:
				return datetime.datetime.strptime(value, "%b %d, %Y")
			except ValueError:
				pass
		return None

	return parser
