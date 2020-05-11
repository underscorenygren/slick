from whisky import items

class WhiskyItemPipeline(object):
	"""fills whisky items fields from name by default"""
	def process_item(self, the_item, spider):
		if isinstance(the_item, items.WhiskyItem):
			the_item = items.fill_item_from_name(the_item)
		return the_item
