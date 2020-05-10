"""metrics package with configurable backends"""
import decimal
from lib import json_formatter, init_logger, split_list, isanyinstance

import boto3
import botocore.exceptions


class PrintBackend(object):
	"""prints metrics as json"""
	NAME_ATTRIBUTE = "metric"

	def publish(self, name, data, dimensions=None, **kwargs):
		"""publishes a metric"""
		data[self.NAME_ATTRIBUTE] = name
		if dimensions:
			data = dict(data, **dimensions)
		print(json_formatter(data))


class NoBackend(object):
	"""dummy backend that discards all metrics"""
	def publish(*args, **kwargs):
		pass


class CloudwatchBackend(object):
	"""logs metrics to cloudwatch"""
	NAMESPACE = 'Steam/Scraping'

	def __init__(self):
		self.cli = boto3.client('cloudwatch', region_name='us-east-1')
		self.logger = init_logger(__name__)

	"""publishes metrics to cloudwatch"""
	def publish(self, name, data, dimensions=None, **kwargs):
		if not data:
			self.logger.info("ignoring empty metric data")
			return

		try:
			dims = [
				{"Name": metric, "Value": value} for (metric, value) in dimensions.items()
			] if dimensions else []
			string, non_string = split_list(data.items(), lambda tupl: isinstance(tupl[1], str))
			# cloudwatch doesn't accept string metrics, so we save them as dims
			# not sure that's the right approach, but it's what we got
			if string:
				for k, v in string:
					dims.append({"Name": k, "Value": v})
			valid, _ = split_list(non_string, lambda tupl: isanyinstance(tupl[1], [int, float, decimal.Decimal]))

			metric_data = [
				{
					"MetricName": f"{name}/{key}",
					"Value": val,
					"Dimensions": dims
				} for key, val in valid]
			if metric_data:
				self.cli.put_metric_data(
					Namespace=self.NAMESPACE,
					MetricData=metric_data)
			else:
				self.logger.debug(f"no metric data parsed from {data}")
		except botocore.exceptions.BotoCoreError:
			self.logger.exception("couldn't record cloudwatch metric")


def get_engine():
	"""creates our defaults metrics engine"""
	return NoBackend()
