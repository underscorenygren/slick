import scrapy
from scrapy.loader import ItemLoader, processors


class BaseItem(scrapy.Item):
	"""base class for items. Items are parsed structured data
	from a web page. Used to specify css/xpaths for how to
	find data and processing methods on how to clean it"""

	"""subclasses can register this attribute to hook in to
	deduplication in item pipeline. Set it to the name of the
	item attribute you want to deduplicate on."""
	_dedup_attribute = None

	"""some pages yield more than one items. Those items
	are kept here and automatically parsed into models"""
	_dependents = []

	def _get_dedup_value(self):
		"""returns value of dedup attr, if registered"""
		return self.get(self._dedup_attribute) if self._dedup_attribute else None

	def get_dependents(self):
		"""gets dependent items for this item, that have
		been registered using add_dependents on the
		corresponfing loader."""
		for dependent_name in self._dependents:
			try:
				yield dependent_name, self[dependent_name]
			except KeyError:
				# dependents can be unset, which is not an error
				pass


class BaseLoader(ItemLoader):
	"""base class for loading items from responses"""
	default_output_processor = processors.TakeFirst()

	_dependents = []

	def add_dependent(self, name, the_item):
		"""adds a dependent item to the item loader"""

		self._dependents.append(name)

		if the_item is not None:
			self.add_value(name, the_item)

	def load_item(self, *args, **kwargs):
		"""subclasses load_item to handle dependents"""
		the_item = super().load_item(*args, **kwargs)
		the_item._dependents = self._dependents

		return the_item
