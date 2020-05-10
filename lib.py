"""containst small, self-contained utility functions"""
import csv
import io
import json
import logging
from urllib.parse import urlparse


def json_serializer(obj):
	"""Defines serialization for objects not covered by json standard"""
	if hasattr(obj, 'isoformat'):
		return obj.isoformat()
	return str(obj)


def json_formatter(obj, **kwargs):
	"""dumps json with our default formatter"""
	return json.dumps(obj, default=json_serializer, **kwargs)


def csv_formatter(arr_of_dict):
	"""writes dictionary as csv"""
	if not arr_of_dict:
		raise ValueError("cannot csv format empty result")
	string_io = io.StringIO()

	first = arr_of_dict[0]
	csv_columns = first.keys()
	writer = csv.DictWriter(string_io, fieldnames=csv_columns, dialect=csv.unix_dialect)
	writer.writeheader()
	for data in arr_of_dict:
		writer.writerow(data)
	return string_io.getvalue()


def _q(r, q, suffix):
	"""shorthand for query"""
	return r.css('{}::{}'.format(q, suffix))


def _get(r, q, suffix):
	"""gets an attribute"""
	return _q(r, q, suffix).get()


def _getall(r, q, suffix):
	"""gets an attribute"""
	return _q(r, q, suffix).getall()


def txt(r, q):
	"""shorthand for getting a link from a query"""
	return _get(r, q, 'text')


def href(r, q, fn=_get):
	"""shorthand for getting one text element from a query"""
	return fn(r, q, 'attr(href)')


def get_domain(url):
	"""gets domain from url"""
	return urlparse(url).netloc


def init_logger(name, level=logging.INFO, handler=None, fmt=None):
	"""initializes a logger"""
	handler = handler or logging.StreamHandler()
	if fmt:
		handler.setFormatter(logging.Formatter(fmt=fmt))
	logger = logging.getLogger(name)
	logger.addHandler(handler)
	logger.setLevel(level)
	return logger


def split_list(lis, splitter):
	"""applies splitting function splitter to list items,
	return two new lists, where the first contains
	all the entries where splitter returns true"""
	left = []
	right = []
	for i in lis:
		if splitter(i):
			left.append(i)
		else:
			right.append(i)
	return left, right


def isanyinstance(o, classes):
	"""calls isinstance on a list of classes.
	true if any matches"""
	for cls in classes:
		if isinstance(o, cls):
			return True
	return False
