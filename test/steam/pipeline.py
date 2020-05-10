from test.steam import fixtures

from slick import model
from steam.models import \
		ConcurrentPlayers, \
		Developer, \
		Game
import lib


logger = lib.init_logger('test.steam.pipeline')


def _upsert(db, the_item, logger=logger):
	model_klass = model.get_model_class_from_item(the_item)
	assert model_klass is not None
	return model.upsert(db, model_klass, the_item, logger=logger)


def test_game_db_upsert(db, game_item, caplog):  # noqa: 401
	game = _upsert(db, game_item, logger=caplog)
	assert game is not None
	dev = game.developer

	# we don't bother checking the values,
	# previous tests handle that
	for col in Game.__table__.columns:
		res = getattr(game, col.name)
		assert res is not None, f"{col.name} missing"

	# make sure ids were set right
	assert game.id is not None
	assert dev.id is not None


def test_developer_db_upsert(db, developer_item, caplog):  # noqa: 401
	"""upserts a developer into the db"""

	dev = _upsert(db, developer_item, logger=caplog)

	# we don't bother checking the values,
	# previous tests handle that
	for col in Developer.__table__.columns:
		res = getattr(dev, col.name)
		assert res is not None, f"{col.name} missing"

	# make sure ids were set right
	assert dev.id is not None

	for key, exp in fixtures.DEVELOPER.items():
		assert getattr(dev, key) is not None


def test_forum_page_db_upsert(db, forum_page_item, caplog): # noqa: 401
	"""upserts a forum page to the db"""

	forum_page = _upsert(db, forum_page_item, logger=caplog)
	dev = forum_page.developer

	assert dev is not None
	assert dev.id is not None
	assert forum_page.id is not None


def test_unicode_developer_db_upsert(db, unicode_developer_item, caplog): # noqa: 401
	"""upserts a developer into the db"""

	dev = _upsert(db, unicode_developer_item, logger=caplog)
	assert dev.id is not None
	assert dev.description is not None


def test_email_db_upsert(db, developer_item, email_item, caplog): # noqa: 401
	"""tests db inserting of emails"""
	dev = _upsert(db, developer_item, logger=caplog)

	assert lib.get_domain(dev.website) == email_item['domain']
	email_item['developer'] = developer_item

	email = _upsert(db, email_item, logger=caplog)

	assert email.id is not None
	assert email.developer_id is not None
	assert email.email == email_item['email']


def test_concurrent_players_insert(db, concurrent_players_item, other_game_item, caplog): # noqa: 401
	"""tests inserting of concurrent players into db"""
	#NB: HTML for this page was changed to conform with tests
	# makes sure game is in DB
	_game = _upsert(db, other_game_item, logger=caplog)
	assert _game is not None
	steam_id = concurrent_players_item.get('steam_id')
	assert steam_id is not None
	game = Game.get_by_steam_id(db, steam_id)
	assert game is not None

	concurrent_players = _upsert(db, concurrent_players_item, logger=caplog)

	assert concurrent_players is not None

	fixtures.assert_concurrent_players_item(concurrent_players_item)
	assert concurrent_players is not None
	fixtures.assert_concurrent_players_model(concurrent_players)

	concurrent_players_obj = ConcurrentPlayers.get_from_item(db, concurrent_players_item)

	assert concurrent_players_obj is not None
	assert concurrent_players_obj.game is not None
	assert concurrent_players_obj.game.name == game.name
	assert concurrent_players_obj.game.id == game.id
