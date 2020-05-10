import datetime
import json

import pytest

import sqlalchemy

import lib
from slick import model, item
from test import session_factory

logger = lib.init_logger("test.slick.model")


class RealizeModel(model.BaseModel):
	"""tests realizing of items"""
	__tablename__ = "realize"

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)


def test_realize_item_class():
	"""tests model -> item"""
	RealizeModel()
	item_class = model.realize_item_class("RealizeItem", RealizeModel)
	item = item_class()
	assert item.get('id') is None
	item['id'] = 1
	assert item['id'] == 1


class SimpleModel(model.BaseModel):
	"""tests back and forth comparison for models<->items"""
	__tablename__ = "simple"

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	field = sqlalchemy.Column(sqlalchemy.String(10))


class ComplexModel(model.BaseModel):
	"""tests back and forth comparison for models<->items on many fields"""
	__tablename__ = "complex"

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	int_ = sqlalchemy.Column(sqlalchemy.Integer)
	str_ = sqlalchemy.Column(sqlalchemy.String(16))
	unicode_ = sqlalchemy.Column(sqlalchemy.Unicode(16))
	float_ = sqlalchemy.Column(sqlalchemy.Float)
	date_ = sqlalchemy.Column(sqlalchemy.DateTime)


class LookupModel(model.BaseModel):
	"""tests realizing of items"""
	__tablename__ = "lookup"

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	field = sqlalchemy.Column(sqlalchemy.String(16))

	_lookup_attributes = ('id', )


class JoiningModel(model.BaseModel):

	__tablename__ = 'joining'

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	joined_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("joined.id"))
	name = sqlalchemy.Column(sqlalchemy.String(16))

	joined = sqlalchemy.orm.relationship("JoinedModel", uselist=False, back_populates="joining")

	_lookup_attributes = ('name', )


class JoinedModel(model.BaseModel):

	__tablename__ = 'joined'

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	name = sqlalchemy.Column(sqlalchemy.String(16))

	joining = sqlalchemy.orm.relationship("JoiningModel", back_populates="joined")

	_lookup_attributes = ('name', )


class PlaceholderModel(model.BaseModel):
	__tablename__ = 'placeholder'

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)

	placeholder = model.Placeholder()


session = session_factory('test.slick.model',
	[SimpleModel, ComplexModel, LookupModel,
		JoiningModel, JoinedModel, PlaceholderModel], logger)


@pytest.fixture()
def db(session):
	"""connection to testing (sqllite) db"""
	sess = session()
	yield sess
	sess.close()


SimpleItem = model.realize_item_class("SimpleItem", SimpleModel)


ComplexItem = model.realize_item_class("ComplexItem", ComplexModel)


LookupItem = model.realize_item_class("LookupItem", LookupModel)


JoiningItem = model.realize_item_class("JoiningItem", JoiningModel)


JoinedItem = model.realize_item_class("JoinedItem", JoinedModel)


PlaceholderItem = model.realize_item_class("PlaceholderItem", PlaceholderModel)


def test_get_model_class():
	item = SimpleItem()
	assert model.get_model_class_from_item(item) == SimpleModel


def test_as_dict():
	field_val = "test"
	mdl = SimpleModel(field=field_val)
	the_time = mdl.updated_at
	_dict = mdl.as_dict()
	assert _dict['field'] == field_val
	assert _dict['created_at'] == the_time
	assert _dict['updated_at'] == the_time


def test_json():
	field_val = "test"
	mdl = SimpleModel(field=field_val)
	_dict = mdl.as_dict()
	loaded = json.loads(mdl.json())
	assert _dict == loaded


def test_simple_assignment():
	val = "test"
	item = SimpleItem()
	item['field'] = val

	mdl_klass = model.get_model_class_from_item(item)
	obj = model.update_model_from_item(mdl_klass(), item)

	assert obj.field == item['field']


def test_complex_assignment():
	item = ComplexItem()

	item['int_'] = 1
	item['str_'] = "string"
	item['unicode_'] = u'A unicode \u018e string \xf1'
	item['float_'] = 2.0
	item['date_'] = datetime.datetime.utcnow()

	mdl_klass = model.get_model_class_from_item(item)
	obj = model.update_model_from_item(mdl_klass(), item)

	assert obj.int_ == item['int_']
	assert obj.str_ == item['str_']
	assert obj.unicode_ == item['unicode_']
	assert obj.float_ == item['float_']
	assert obj.date_ == item['date_']


def test_joining_model():
	"""tests items from models with relationships are auto-wired"""
	item = JoiningItem(joined='something')
	assert item['joined'] is not None

def test_simple_upsert(db, caplog):
	val = "test"
	item = SimpleItem()
	item['field'] = val

	model_klass = model.get_model_class_from_item(item)

	# doesn't have lookup values registered
	with pytest.raises(ValueError):
		model.upsert(db, model_klass, item, logger=caplog)


def test_lookup_upsert(db, caplog):
	val = 1
	field1 = "field1"
	field2 = "field2"

	item = LookupItem()
	item['id'] = val
	item['field'] = field1

	model_klass = model.get_model_class_from_item(item)

	obj = model.upsert(db, model_klass, item, logger=caplog)
	db.commit()

	assert obj.id == val
	assert obj.field == field1

	item['field'] = field2
	obj = model.upsert(db, model_klass, item, logger=caplog)
	db.commit()

	assert obj.field == field2

	lookup = model_klass.get_from_item(db, LookupItem(id=val))
	assert lookup == obj


def test_joined_upsert(db):

	joining_name = 'joining'
	joined_name = 'joined'

	joined_item = JoinedItem(name=joined_name)

	joining_loader = item.BaseLoader(JoiningItem())
	joining_loader.add_value('name', joining_name)
	joining_loader.add_dependent('joined', joined_item)

	joining_item = joining_loader.load_item()

	assert joined_item['name'] == joined_name
	assert joining_item['name'] == joining_name

	out = model.upsert(db, JoiningModel, joining_item)
	assert out is not None

	found_joining = JoiningModel.get_from_item(db, joining_item)
	assert found_joining is not None

	found_joined = JoinedModel.get_from_item(db, joined_item)
	assert found_joined is not None

	assert found_joining.joined == found_joined


def test_doesnt_set_primary_or_foreign_keys(db):

	joining_name = 'joining2'
	joined_name = 'joined2'

	joined_item = JoinedItem(name=joined_name, joining=['should be eliminated'])

	joining_item = JoiningItem(name=joining_name, joined_id=1)

	joined_model = model.create_model_from_item(joined_item)

	joining_model = model.create_model_from_item(joining_item)

	assert joined_model.name == joined_name
	assert joining_model.name == joining_name

	assert joining_model.joined_id is None
	assert bool(joined_model.joining) is False


def test_placeholder():
	plc = "something"
	item = PlaceholderItem(placeholder=plc)
	mdl = model.create_model_from_item(item)
	assert mdl.placeholder == plc
