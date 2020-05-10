import hashlib

from slick import model

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class Game(model.BaseModel):
	"""Game data model"""

	__tablename__ = "game"
	_lookup_attributes = ('name', )

	id = Column(Integer, primary_key=True)
	name = Column(String(256), unique=True)
	developer_id = Column(Integer, ForeignKey("developer.id"), index=True)
	steam_id = Column(Integer, index=True)
	url = Column(String(256))
	release_date = Column(DateTime(), index=True)
	on_macos = Column(Boolean, default=False, index=True)
	on_windows = Column(Boolean, default=False, index=True)
	on_linux = Column(Boolean, default=False, index=True)

	developer = relationship("Developer", uselist=False, back_populates="games")
	search_results = relationship("SteamSearchResult", back_populates="game")
	forum_pages = relationship("ForumPage", back_populates="game")
	concurrent_players = relationship("ConcurrentPlayers", back_populates="game")

	@staticmethod
	def get_by_steam_id(db, steam_id):
		return db.query(Game).filter(Game.steam_id == steam_id).one_or_none()


class Developer(model.BaseModel):
	"""Developer data model"""

	__tablename__ = "developer"
	_lookup_attributes = ('name', )

	id = Column(Integer, primary_key=True)
	name = Column(String(256), unique=True)
	description = Column(String(256), index=True)
	steam_id = Column(String(64), index=True)
	steam_url = Column(String(256))
	website = Column(String(256))
	steam_followers = Column(Integer, index=True)
	facebook_followers = Column(Integer, index=True)
	twitch_followers = Column(Integer, index=True)
	twitter_followers = Column(Integer, index=True)
	youtube_followers = Column(Integer, index=True)

	games = relationship("Game", back_populates="developer")
	forum_pages = relationship("ForumPage", back_populates="developer")
	emails = relationship("Email", back_populates="developer")

	url = model.Placeholder()

	@staticmethod
	def get_by_domain(db, val):
		return db.query(Developer)\
			.filter(Developer.website.like(f'%{val}%'))\
			.first()


class ForumPage(model.BaseModel):

	__tablename__ = "forum_page"
	_lookup_attributes = ('url', )

	id = Column(Integer, primary_key=True)
	url = Column(String(256), index=True)
	developer_id = Column(Integer, ForeignKey("developer.id"), index=True)
	game_id = Column(Integer, ForeignKey("game.id"), index=True)

	developer = relationship("Developer", uselist=False, back_populates="forum_pages")
	game = relationship("Game", uselist=False, back_populates="forum_pages")


class Email(model.BaseModel):
	__tablename__ = "email"
	_lookup_attributes = ('email', )

	id = Column(Integer, primary_key=True)
	email = Column(String(256), unique=True)
	url = Column(String(256), index=True)
	domain = Column(String(128), index=True)

	developer_id = Column(Integer, ForeignKey("developer.id"), index=True)

	developer = relationship("Developer", uselist=False,
			back_populates="emails")


class UrlCache(model.BaseModel):
	"""we store urls here while they process so we can interrupt crawls and restart them"""

	__tablename__ = "url_cache"

	crawl_name = Column(String(32), index=True, primary_key=True)
	url_hash = Column(String(64), index=True, primary_key=True)
	url = Column(String(512), index=True)
	callback = Column(String(64))
	crawled = Column(Boolean, default=0)

	@staticmethod
	def make(spider, request_or_response):
		url = request_or_response.url
		callback = None
		try:
			callback = request_or_response.callback.__name__
		except AttributeError:
			pass
		m = hashlib.md5()
		m.update(url.encode('utf8', 'ignore'))
		return UrlCache(
			crawl_name=spider.name,
			url_hash=m.hexdigest(),
			callback=callback,
			url=url)

	@staticmethod
	def insert(spider, response):
		db = spider.db
		db.add(UrlCache.make(spider, response))
		try:
			db.commit()
		except Exception:
			db.rollback()

	@staticmethod
	def resolve(spider, response):
		"""marks a url as crawled"""
		db = spider.db
		cached = UrlCache.make(spider, response)
		db.query(UrlCache).filter(
			UrlCache.crawl_name == cached.crawl_name,
			UrlCache.url_hash == cached.url_hash)\
			.update({UrlCache.crawled: 1})
		try:
			db.commit()
		except Exception:
			db.rollback()

	@staticmethod
	def get(db, name):
		return db.query(UrlCache).filter(
			UrlCache.crawl_name == name,
			UrlCache.crawled == 0)


class SteamSearchResult(model.BaseModel):
	"""search result model - maps tags to games"""

	__tablename__ = "steam_search_result"
	_lookup_attributes = ('name',)

	id = Column(Integer, primary_key=True)
	name = Column(String(128), index=True)
	tag_name = Column(String(64), index=True)
	tag_value = Column(String(64), index=True)
	game_id = Column(Integer, ForeignKey("game.id"), index=True)

	game = relationship("Game", back_populates="search_results", uselist=False)


class ConcurrentPlayers(model.BaseModel):

	__tablename__ = "concurrent_players"
	_lookup_attributes = ('steam_id',)

	id = Column(Integer, primary_key=True)
	game_id = Column(Integer, ForeignKey("game.id"), unique=True)
	steam_id = Column(Integer, index=True)
	current = Column(Integer, index=True)
	daily = Column(Integer, index=True)
	monthly = Column(Integer, index=True)
	all_time = Column(Integer, index=True)

	game = relationship("Game", back_populates="concurrent_players", uselist=False)
