# -*- coding: utf-8 -*-
import inspect
from scrapy.exceptions import DropItem

from slick import model

ITEM_CLASS_ATTRIBUTE = "_item_classes"


class ItemDeduplicators(object):
	"""A generic way to handle deduplication

	Supported items have a deduplication attribute,
	which this class checks and against duplicates stored
	internally as a set in memory"""

	def __init__(self, klasses=[]):
		self.dedupers = {klass: set() for klass in klasses}

	def is_duplicate(self, item):
		"""checks if item is duplicate. Adds it to set if it is.
		Returns true iff item is duplicate, false otherwise"""
		if not self._supports_dedup(item):
			return False

		for im, deduper in self.dedupers.items():
			if im.match(item):
				dedup_val = self._get_dedup_value(item)
				if dedup_val is not None:
					if dedup_val in deduper:
						return True
					deduper.add(dedup_val)

		return False


def get_default_import_string(spider):
	"""the default import string for a spider is [spider.name].items"""
	return f"{spider.__name__}.items"


# TODO add custom setting
def yield_item_classes(import_string=None):
	"""finds all item classes registered in the import_string scope"""
	if import_string is None:
		import_string = get_default_import_string()
	for name, obj in inspect.getmembers(import_string):
		if inspect.isclass(obj):
			yield obj


class ItemDeduplicationPipeline(object):
	"""uses dudplication logic to drop items"""

	def open_spider(self, spider):
		"""registers deduplicator instance on spider"""
		super(ItemDeduplicationPipeline, self).open_spider(spider)
		self.deduplicator = ItemDeduplicators([c for c in yield_item_classes()])

	def process_item(self, item, spider):
		"""drops item on duplication"""
		item = super(ItemDeduplicationPipeline, self).process_item(item, spider)

		if self.deduplicator.check_duplicate(item):
			raise DropItem("item is duplicate")

		return item


class DBPipeline(object):
	"""inserts crawl objects to db"""

	def open_spider(self, spider, db=None):
		"""opens db connection"""
		try:
			super(DBPipeline, self).open_spider(spider)
		except AttributeError:
			pass
		self.db = model.SqlSession() if db is None else db
		found_item_classes = False
		try:
			found_item_classes = getattr(spider, ITEM_CLASS_ATTRIBUTE)
		except AttributeError:
			pass

		if not found_item_classes:
			raise ValueError(f"no {ITEM_CLASS_ATTRIBUTE} registered on spider {spider}")

		self.item_classes = [c for c in found_item_classes]

	def close_spider(self, spider):
		"""close db on spider close"""
		try:
			super(DBPipeline, self).close_spider(spider)
		except AttributeError:
			pass
		self.db.close()

	def process_item(self, item, spider):
		"""Processes an item by matching it to
		a model class (if it has one) and calling upsert."""
		try:
			item = super(DBPipeline, self).process_item(item, spider)
		except AttributeError:
			pass

		for klass in self.item_classes:
			if isinstance(item, klass):
				model_klass = model.get_model_class_from_item(item)
				if model_klass is None:
					raise DropItem(f"{item} has not registered model.")

				item = model.upsert(self.db, model_klass, item, logger=spider.logger)

				# each item can only have one model class, so we break
				break

		return item
