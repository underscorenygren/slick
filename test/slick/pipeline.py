import pytest

import sqlalchemy

import lib
from slick import model, pipeline
from test import session_factory


class PipelineModel(model.BaseModel):
	"""tests pipeline processing of items"""
	__tablename__ = "pipeline"

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	field = sqlalchemy.Column(sqlalchemy.String(16))

	_lookup_attributes = ('id', )


PipelineItem = model.realize_item_class("PipelineItem", PipelineModel)

logger = lib.init_logger("test.slick.pipeline")
session = session_factory('test.slick.pipeline', [PipelineModel], logger)


@pytest.fixture()
def db(session):
	"""connection to testing (sqllite) db"""
	sess = session()
	yield sess
	sess.close()


class Pipeline(pipeline.DBPipeline):
	"""needs no implementation itself"""
	pass


class PipelineSpider(object):
	"""not depending on scrapy b/c we don't need to"""
	_item_classes = (PipelineItem, )
	name = "test.slick.pipeline"
	logger = logger


def test_db_pipeline(db):
	pipeliner = Pipeline()
	spider = PipelineSpider()
	pipeliner.open_spider(spider, db=db)

	_id = 1
	field = "field"

	item = PipelineItem(id=_id, field=field)

	processed = pipeliner.process_item(item, spider)

	assert isinstance(processed, PipelineModel)

	found = db.query(PipelineModel).get(_id)
	assert found == processed

	pipeliner.close_spider(spider)
