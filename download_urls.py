"""
downloads test urls, so we can avoid keeping them in git
"""
urls = {
	"steam_local_coop_tag": 'https://store.steampowered.com/search/?tags=1685',
	"steam_tags_search_result": 'https://store.steampowered.com/search/?term=Tom+Clancy%27s+Rainbow+Six%C2%AE+Siege',
	'game': 'https://store.steampowered.com/app/359550/Tom_Clancys_Rainbow_Six_Siege/?snr=1_7_7_151_150_1',
	'other_game': 'https://store.steampowered.com/app/320040/Moon_Hunters/',
	"forum_page": 'https://steamcommunity.com/app/285900/discussions/2/1696095174287969149/',
	"pythonorg": 'https://www.python.org/',
	"dekanta_search": "https://dekanta.com/store/?orderby=date",
	'dekanta_item': 'https://dekanta.com/store/yamazaki-12-year-old-single-malt-final-version/',
	"email": 'http://cellardoorgames.com/contact/',
	"grand_search": 'https://www.thegrandwhiskyauction.com/april-2020',
	"developer": 'https://store.steampowered.com/developer/kitfoxgames',
	"unicode_developer": 'https://store.steampowered.com/developer/TUQUE',
	"concurrent_players": 'https://steamcharts.com/app/320040',
	"steam_charts_top": 'https://steamcharts.com/top',
}

if __name__ == "__main__":
	import requests

	for name, url in urls.items():
		with open(f'test/data/{name}.html', 'wb') as f:
			print(f"getting {url}")
			req = requests.get(url)
			print(f"writing to {name}")
			f.write(req.content)
