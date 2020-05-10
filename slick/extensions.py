"""Extensions we add to our crawlers.

See https://github.com/scrapy/scrapy/blob/master/scrapy/extensions/logstats.py
for inspiration."""
from twisted.internet import task
from scrapy import signals
from scrapy.exceptions import NotConfigured

import metrics


class PublishMetricsExtension(object):
	def __init__(self, stats, interval):
		"""initilaizes looping call"""
		self.metrics = metrics.get_engine()
		self.stats = stats
		self.interval = interval
		self.spider_name = ''

	def spider_opened(self, spider):
		"""starts publishing task"""

		self.spider_name = spider.name
		self.task = task.LoopingCall(self.log)
		self.task.start(self.interval)

	@classmethod
	def from_crawler(cls, crawler):
		"""initializing from crawler"""
		interval = crawler.settings.getfloat('PUBLISHMETRICS_INTERVAL')
		if not interval:
			raise NotConfigured("no interval for metrics publishing")
		o = cls(crawler.stats, interval)
		crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
		crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
		return o

	def log(self):
		"""logs the stats"""
		stats = {k: v for (k, v) in self.stats.get_stats().items() if k.find('log_count') == -1}
		# first stats call only has log info
		if stats:
			self.metrics.publish('stats', stats, dimensions={"spider": self.spider_name})

	def spider_closed(self, spider, reason):
		"""stops task on spider end"""
		if self.task and self.task.running:
			self.task.stop()
