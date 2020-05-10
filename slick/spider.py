from slick import model
from metrics import get_engine


class DBMixin(object):
	"""holds a connection to the DB"""
	def __init__(self, *args, **kwargs):
		"""opens db"""
		super().__init__(*args, **kwargs)
		self.db = model.SqlSession()

	def closed(self, reason):
		"""closes db"""
		self.db.close()


class MetricsMixin(object):
	"""holds a connection to a metrics backend"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.metrics = get_engine()

	def metric(self, name, data, **kwargs):
		"""publishes a metric"""
		self.metrics.publish(name, data, dimensions={"spider": self.name}, **kwargs)
