import pytest

import sqlalchemy

from slick import model, item
import test


PYTHONORG_URL = 'https://python.org'


class PythonOrgModel(model.BaseModel):
	__tablename__ = "test_pythonorg"

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	txt = sqlalchemy.Column(sqlalchemy.String(64))
	logo = sqlalchemy.Column(sqlalchemy.String(model.URL_LENGTH))
	url = sqlalchemy.Column(sqlalchemy.String(model.URL_LENGTH))


PythonOrgItem = model.realize_item_class("PythonOrgItem", PythonOrgModel)


def load(response):
	loader = item.BaseLoader(PythonOrgItem(), response=response)
	url = response.url

	loader.add_xpath('txt', '//*[@id="content"]/div/section/div[1]/div[1]/h2/text()[1]')
	loader.add_css('logo', 'img.python-logo::attr(src)')
	loader.add_value('url', url)

	return loader.load_item()


@pytest.fixture()
def pythonorg_response():
	"""game item loaded from html file"""
	return test.fake_response_from_file('pythonorg.html', url=PYTHONORG_URL)


def test_load_item(pythonorg_response):

	txt_ref = 'Get Started'
	logo_ref = '/static/img/python-logo.png'
	url_ref = PYTHONORG_URL

	item = load(pythonorg_response)
	assert item['txt'] == txt_ref
	assert item['logo'] == logo_ref
	assert item['url'] == url_ref
