"""unit testing"""


import os

import pytest
import sqlalchemy
from scrapy.http import HtmlResponse, Request
from sqlalchemy.orm import sessionmaker

RESPONSES_SUBDIR = 'data'

# https://stackoverflow.com/questions/6456304/scrapy-unit-testing
def fake_response_from_file(file_name, url=None):
		"""
		Create a Scrapy fake HTTP response from a HTML file
		@param file_name: The relative filename from the responses directory,
											but absolute paths are also accepted.
		@param url: The URL of the response.
		returns: A scrapy HTTP response which can be used for unittesting.
		"""
		if not url:
				url = 'http://www.example.com'

		request = Request(url=url)
		if not file_name[0] == '/':
				responses_dir = os.path.dirname(os.path.realpath(__file__))
				file_path = os.path.join(responses_dir, RESPONSES_SUBDIR, file_name)
		else:
				file_path = file_name

		file_content = ''
		try:
			with open(file_path, 'r') as f:
				file_content = f.read()
		except FileNotFoundError as e:
			print("Couldn't find test file, did you forget to call make download-fixtures?")
			raise e

		response = HtmlResponse(url=url,
				request=request,
				body=file_content,
				encoding='utf-8')
		return response


def session_factory(name, models, logger):
	"""creates a session by making models in a sqllite file"""
	@pytest.fixture(scope='module')
	def _session():
		db_file = '{}.db'.format(name)
		try:
			os.unlink(db_file)
		except OSError:
			pass

		conn_str = 'sqlite:///{}'.format(db_file)
		engine = sqlalchemy.create_engine(conn_str,
				poolclass=sqlalchemy.pool.NullPool)

		for mod in models:
			logger.debug("creating {}".format(mod))
			try:
				_table = mod.__table__ if hasattr(mod, '__table__') else mod
				_table.create(engine)
			except Exception as err:
				str_err = str(err)
				if str_err.find('FULLTEXT') > -1:
					logger.info("attempting to ignore FULLTEXT error")
				else:
					raise err

		yield sessionmaker(bind=engine)
		# code below yield is teardown (neat)
		os.unlink(db_file)
	return _session
