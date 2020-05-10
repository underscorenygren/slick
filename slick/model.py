"""data storage"""
import datetime
import json
from contextlib import contextmanager

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
import scrapy

import env
import lib
from slick import parser, item


DEFAULT_ENGINE_ARGS = {
	'connect_args': {
		"connect_timeout": 1
	},
	'isolation_level': 'READ_COMMITTED',
	'poolclass': sqlalchemy.pool.StaticPool,
	'pool_recycle': 5 * 60,
}
ITEM_MODEL_ATTRIBUTE = '_model_klass'
DEFAULT_COLLATION = 'utf8mb4_unicode_ci'
URL_LENGTH = 512


logger = lib.init_logger("slick.model")


def truncated_nowfn():
	"""nowfn where microseconds are always 0"""
	return datetime.datetime.utcnow().replace(microsecond=0)


def get_engine(user=None, password=None, host=None, port=None, db=None, charset=None, **kwargs):
	"""Gets sqlalchemy engine. Can also be configured using environment variables."""
	# We use a null pool since we don't have that much load, and want to avoid Ops errors.
	# http://docs.sqlalchemy.org/en/latest/core/pooling.html#sqlalchemy.pool.SingletonThreadPool
	# Singleton is discouraged in production, and I've seen intermittend 'Mysql has gone away' erorrs with it
	_args = dict(DEFAULT_ENGINE_ARGS, **kwargs)
	mysql_dict = {
		"user": user or env.mysql_user,
		"password": password or env.mysql_password,
		"host": host or env.mysql_host,
		"port": port or env.mysql_port,
		"db": db or env.mysql_db,
		"charset": charset or env.mysql_charset,
	}

	mysql_str = u"mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset={charset}".format(**mysql_dict)

	return sqlalchemy.create_engine(mysql_str, **_args)


class BaseObject(object):
	"""base class for models"""

	"""Use to filter out columns when printing obj using as_dict and json"""
	_filter_columns = []
	"""Use to assign custom functions to attributes when mapping items to models"""
	_getters = {}
	"""use to avoid setting these attributes on the model, because they conflict with non-write attributes"""
	_do_not_set_attributes = []
	"""use to automatically wire db queries for looking up models from items"""
	_lookup_attributes = []

	updated_at = sqlalchemy.Column(sqlalchemy.DateTime(), onupdate=truncated_nowfn, default=truncated_nowfn, index=True)
	created_at = sqlalchemy.Column(sqlalchemy.DateTime(), default=truncated_nowfn, index=True)

	updated_at._creation_order = 1000
	created_at._creation_order = 1001

	def as_dict(self, **kwargs):
		"""Get object as a dictionary"""
		filter_columns = self._filter_columns if hasattr(self, '_filter_columns') else []
		columns = [c for c in self.__table__.columns if c.name not in filter_columns]
		return {c.name: getattr(self, c.name) for c in columns}

	def json(self, **kwargs):
		"""Get json string representation of object"""
		if 'default' not in kwargs:
			kwargs['default'] = lib.json_serializer
		return json.dumps(self.as_dict(), **kwargs)

	@classmethod
	def get_from_item(cls, db, the_item):
		"""this function is auto-wired using the _lokup_attributes registered on the class,
		and constructs a sqlalchemy filter one_or_none query using them."""
		model_klass = getattr(the_item, ITEM_MODEL_ATTRIBUTE)
		if model_klass is None:
			raise ValueError(f"no model class registered on item, did you make it using model.realize_item?")

		attributes = [getattr(cls, attr) == the_item[attr] for attr in cls._lookup_attributes]
		if not attributes:
			raise ValueError(f"no _lookup_attributes registered on {cls.__name__}")

		return db.query(model_klass).filter(*attributes).one_or_none()


class Placeholder(object):
	"""adds fields to the item derived from a model, but doesn't
	added them to the model.
	Used to signal that a field is needed in the parsing (like a url field for traversal)
	what we don't want inserted into the DB.
	"""
	pass


def get_model_class_from_item(the_item):
	"""returns the registered model class for an item,
	or None if nothing is registered, e.g. item
	has not been created from model.realize_item"""
	try:
		return getattr(the_item, ITEM_MODEL_ATTRIBUTE)
	except AttributeError:
		return None

class ReloadableSession(object):
	"""wrapper around session, to register
	custom _reload function that rebinds engine"""

	def __init__(self):
		self.session = sqlalchemy.orm.sessionmaker(bind=get_engine())

	def __call__(self):
		return self.session()

	def _reload(self):
		self.session = sqlalchemy.orm.sessionmaker(bind=get_engine())


"""The base class for SQLAlchemy models that we register"""
BaseModel = declarative_base(cls=BaseObject)  # SQLAlchemy syntax fore registering our custom base class

"""The global session constructor class"""
SqlSession = ReloadableSession()


def get_registered_models():
	"""gets models that have subclassed BaseModel, e.g. are "pipelineable"."""
	return BaseModel.__subclasses__()


def rebind():
	"""rebinds model engine for sessions,
	such as when env variables change"""
	SqlSession._reload()


@contextmanager
def db_context(**kwargs):
	"""wraps new sql session in a context
	that commits and closes automatically,
	allowing with keyword to be used."""

	session = None
	try:
		session = SqlSession()
		yield session
	except Exception:
		session.rollback()
		raise
	else:
		session.commit()
	finally:
		session.close()

def _is_one_col_match_key(key, col_list):
	"""true iff key is the primary key on an object
	that defines a simple (non-compound) primary key"""
	if len(col_list) == 1:
		col = col_list[0]
		if col.name == key:
			return True
	return False

def _is_primary_key(key, obj):
	"""true iff key is the primary key on an object
	that defines a simple (non-compound) primary key"""
	model_klass = obj.__class__
	primary_keys = model_klass.__mapper__.primary_key
	return _is_one_col_match_key(key, primary_keys)


def _is_foreign_key(key, obj):
	for column in obj.__class__.__table__.c:
		if column.name == key and column.foreign_keys:
			return True
	return False


def update_model_from_item(obj, the_item):
	"""sets all matching fields on db model from item"""
	item_dependents = [name for name, _ in the_item.get_dependents()]
	for key, value in the_item.items():
		if key[0] != '_' and \
				hasattr(obj, key) and \
				key not in obj.__class__._do_not_set_attributes and \
				key not in item_dependents and \
				not _is_primary_key(key, obj) and \
				not _is_foreign_key(key, obj) and \
				key not in _get_relationship_properties(obj.__class__):
			setattr(obj, key, value)

	for key, getter in obj._getters.items():
		setattr(obj, key, getter(the_item))

	return obj


def new_model_from_item(klass, the_item):
	"""creates a new model from a item class"""
	return update_model_from_item(klass(), the_item)


def create_model_from_item(the_item):
	"""creates a new model from just item by looking up class"""
	return new_model_from_item(get_model_class_from_item(the_item), the_item)


def sqlalchemy_column_to_field(col, processors=None):
	"""creates a scrapy.Field() from a sqlalchemy column.

	Note that all classes from sqlalchemy are registered, so
	make sure you add them here if you start relying on new ones."""

	default_processors = []

	_type = col.type

	if isinstance(_type, sqlalchemy.Integer):
		default_processors = [
			parser.strip_tags,
			parser.strip_whitespace,
			parser.read_int]

	elif isinstance(_type, sqlalchemy.String):
		default_processors = [
			parser.strip_whitespace]

	elif isinstance(_type, sqlalchemy.Unicode):
		default_processors = [
			parser.strip_whitespace]

	elif isinstance(_type, sqlalchemy.Float):
		default_processors = [
			parser.strip_tags,
			parser.strip_whitespace,
			parser.read_float]

	elif isinstance(_type, sqlalchemy.Boolean):
		# detects presence of tags
		default_processors = [lambda x: True if x is not None else False]
		# parser.strip_tags,
		# parser.strip_whitespace,
		# parser.read_bool]

	elif isinstance(_type, sqlalchemy.DateTime):
		pass

	else:
		raise NotImplementedError(f"Missing column to field mapping for {col}-{_type}")

	processors = processors if processors is not None else []
	all_processors = default_processors + processors

	if not all_processors:
		return scrapy.Field()

	return scrapy.Field(
		input_processor=scrapy.loader.processors.MapCompose(
			*all_processors))


def _get_relationship_properties(model_klass):
	for relationship_property in model_klass.__mapper__.relationships:
		yield str(relationship_property).split('.')[-1]


def realize_item_class(klassname, model_klass):
	"""creates a Scrapy.Item class from a sqlalchemy definition"""
	fields = {column.name: sqlalchemy_column_to_field(column) for column in model_klass.__table__.columns}
	fields[ITEM_MODEL_ATTRIBUTE] = model_klass

	# any joined realtinship can be a field on an item.
	# However, they include no mappers, they are added "raw"
	# There's probably a better name to get the "name" of the property,
	# this is the first I came up with
	extra_fields = [prop for prop in _get_relationship_properties(model_klass)]
	# Adds any registered Placeholder
	for attr_name in dir(model_klass):
		if isinstance(getattr(model_klass, attr_name), Placeholder):
			extra_fields.append(attr_name)

	for field_name in extra_fields:
		fields[field_name] = scrapy.Field()

	return type(klassname,
			(item.BaseItem, ),
			fields)


def insert(db, realized_model, the_item, logger=logger, **kwargs):
	"""inserts a model object into the db.
	Assumes it's already been added/merged
	to session.
	Swallows and logs exceptions"""

	#out = {
	#	"item": the_item,
	#	"model": realized_model.as_dict(),
	#	"related": {}}

	# TODO
	# for related_attr, related_klass in self.get_related():
	# obj = related_klass.get_or_make(db, the_item, logger=logger)
	# assigns to sqlalchemy model so foreign keys are inserted
	# setattr(existing, related_attr, obj)
	# assign to processed to returned item
	# out['related'][related_attr] = obj.as_dict()

	try:
		db.commit()
	except sqlalchemy.exc.SQLAlchemyError:
		db.logger()
		if logger:
			logger.exception(f"couldn't insert {the_item}")

	return realized_model


def _get_or_create(db, model_klass, the_item, **kwargs):
	"""looks up object, creates new if not found"""
	existing = model_klass.get_from_item(db, the_item)

	if existing:
		update_model_from_item(existing, the_item)
	else:
		# constructs a new empty instance and adds it
		existing = update_model_from_item(model_klass(), the_item)
		# adds to session so it's inserted
		db.add(existing)

	for dependent_name, dependent_item in the_item.get_dependents():
		if not hasattr(existing, dependent_name):
			raise ValueError(f"'{dependent_name}' is not an attribute on {existing.__class__}")
		dependent_model_class = get_model_class_from_item(dependent_item)
		if not dependent_model_class:
			raise ValueError(f"dependent model {dependent_name} can not be realized to model")

		dependent_model = _get_or_create(db,
				dependent_model_class,
				dependent_item,
				**kwargs)

		setattr(existing, dependent_name, dependent_model)

	return existing


def upsert(db, model_klass, the_item, **kwargs):
	"""looks up object from the_item, does insert
	iff new object created."""
	existing = _get_or_create(db, model_klass, the_item, **kwargs)
	out = insert(db, existing, the_item, **kwargs)

	return out
