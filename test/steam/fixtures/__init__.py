import datetime

GAME_URL = 'https://store.steampowered.com/app/359550/Tom_Clancys_Rainbow_Six_Siege/?snr=1_7_7_151_150_1'
OTHER_GAME_URL = 'https://store.steampowered.com/app/320040/Moon_Hunters/'
DEVELOPER_URL = 'https://store.steampowered.com/developer/kitfoxgames'
FORUM_URL = 'https://steamcommunity.com/app/285900/discussions/2/1696095174287969149/'

DEVELOPER = {
	"name": "Kitfox Games",
	"description": "We create intriguing worlds that are different every time. We're a small team in Montreal, Canada, and we hope you enjoy our games!",
	"steam_id": "kitfoxgames",
	"steam_url": "https://store.steampowered.com/developer/kitfoxgames",
	"website": "http://www.kitfoxgames.com",
	"steam_followers": 882,
	"facebook_followers": 3035,
	"twitch_followers": 616,
	"twitter_followers": 10362,
	"youtube_followers": 1151
}
GAME_STEAM_ID = 320040
GAME = {
	"steam_id": GAME_STEAM_ID,
	"url": GAME_URL,
	"name": "Moon Hunters",
	"release_date": datetime.datetime.fromisoformat('2016-03-10'),
	"on_macos": True,
	"on_windows": True,
	"on_linux": True}


def assert_concurrent_players_item(concurrent_players_item):
	"""asserts concurrent players item. repeated so in separate fn"""
	assert concurrent_players_item is not None
	assert concurrent_players_item.get('steam_id') is not None
	assert concurrent_players_item.get('current') > 0
	assert concurrent_players_item.get('daily') > 0
	assert concurrent_players_item.get('monthly') > 0
	assert concurrent_players_item.get('all_time') > 0


def assert_concurrent_players_model(concurrent_players_model):
	"""asserts concurrent players item. repeated so in separate fn"""
	assert concurrent_players_model is not None
	assert concurrent_players_model.steam_id is not None
	assert concurrent_players_model.current > 0
	assert concurrent_players_model.daily > 0
	assert concurrent_players_model.monthly > 0
	assert concurrent_players_model.all_time > 0
