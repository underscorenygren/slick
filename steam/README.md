# Steam

This scraper gets game and popularity data from steam and steamcharts.

Each scraper is detailed below.

```
docker-compose exec app scrapy crawl [spider_name]
```

### `forum`

This scraper searches steam forums for the keyword passed in as a env param, and attempts to follow the results
to discover a developer from the forum discussion. The steam forums have a robot-guard which bans you if you crawl too
quickly, so it has a delay built in. This crawl yields `forum_page` and `developer` data models.

To see which developers have been discovered via forum, you developers against forum pages, see
```
docker-compose exec app python cli.py forums --print
```

### `tags`

This scraper searches the steamstore using tags, (currently the local coop tag), to discover game and developer data.
It yields `game` and `developer` objects.

To see which developers have been discovered via forum pages, see
```
docker-compose exec app python cli.py tags --print
```

### `email`

This scraper looks up developers in our DB that have a `website` field in the DB (parsed through a different spider).
It takes this as a starting point, then crawls their entire domain to try to discover emails. We have had some limited success with this, and it's still very much
A work in progress.


### `concurrent_players`

Gathers statistics from https://steamcharts.com , which shows how many players are playing a steam game for certain times. Looks up the potential games from what's in the DB.
Yields `concurrent_players` objects.
