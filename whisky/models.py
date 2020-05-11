from sqlalchemy import Column, Integer, String, Float, DateTime, Unicode

from slick import model


class WhiskySearchResult(model.BaseModel):

	__tablename__ = "whisky_search_result"
	_filter_columns = ['id']
	_lookup_attributes = ('name',)

	id = Column(Integer, primary_key=True)
	name = Column(Unicode(512, collation=model.DEFAULT_COLLATION), unique=True)
	price = Column(Float())
	currency = Column(String(16))
	domain = Column(String(128))
	url = Column(String(512))


class Whisky(model.BaseModel):
	__tablename__ = "whisky"
	_filter_columns = ['id']
	_lookup_attributes = ('name',)

	id = Column(Integer, primary_key=True)

	name = Column(Unicode(512, collation=model.DEFAULT_COLLATION), unique=True)
	price = Column(Float())
	currency = Column(String(16))
	distillery = Column(String(64))
	origin = Column(String(64))
	sold_date = Column(DateTime())
	abv = Column(Float())
	cask_no = Column(String(64))
	cask_type = Column(String(256))
	size = Column(Integer)
	vintage = Column(Integer)
	age = Column(Integer)
	url = Column(String(512))
	domain = Column(String(128))
