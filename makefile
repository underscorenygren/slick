.PHONY: help install create up down build mysql test crawl_forum crawl_tags whisky


# From: https://suva.sh/posts/well-documented-makefiles/#grouped-makefile
BLUESTYLE=\033[36m
REDSTYLE=\033[31m
BOLDSTYLE=\033[1m
ENDSTYLE=\033[0m
PADDING=25
PADDINGSTR=$(shell printf "%-${PADDING}s" ' ')
HELP_AWK_CMD=$\
	BEGIN { $\
		FS = ":.*\#\#"; $\
		print "Usage:\n", $\
		"make $(BLUESTYLE)<command>$(ENDSTYLE)" $\
	} $\
	/^[\\%%a-zA-Z_-]+:.*?\#\#/ { $\
		printf "$(BLUESTYLE)%-$(PADDING)s$(ENDSTYLE) %s\n", $$1, $$2 $\
	} $\
	/^\#\#@/ { $\
		printf "\n$(BOLDSTYLE)%s$(ENDSTYLE)\n", substr($$0, 5) $\
	}

help:
	$(eval WIDTH=90)
	@awk '$(HELP_AWK_CMD)' Makefile | while read line; do \
        if [[ $${#line} -gt $(WIDTH) ]] ; then \
			echo "$$line" | fold -sw$(WIDTH) | head -n1; \
			echo "$$line" | fold -sw$(WIDTH) | tail -n+2 | sed "s/^/  $(PADDINGSTR)/"; \
		else \
			echo "$$line"; \
		fi; done

#####################################
## End of Makefile self-documentation

##@ Setup

install: build up create down download-fixtures ## builds docker image and creates local tables
	@echo "installed"

download-fixtures:  ## downloads test html files
	python download_urls.py

build:  ## builds docker images
	docker-compose build

create:  ## creates DB tables
	docker-compose run app cli.py create

recreate:  ## recreates DB tables
	docker-compose run app cli.py recreate

whisky:  ## runs whisky crawler
	docker-compose run -v $(PWD)/credentials.json:/opt/credentials.json -v $(PWD)/token.pickle:/opt/token.pickle app whisky.py query --name Whisky --sheet '1rYKqYA67MpM2nY0T6pCTzDea6vM9fX1GJT3Iv3Ono14'

##@ Running

up:  ## starts docker application in the background
	docker-compose up --force-recreate -d

down:  ## stops docker compose application
	docker-compose down

logs:  ## tails logs in app container
	docker-compose logs -f app

crawl_forum:  ## runs forum spider
	docker-compose exec -T -e SCRAPY_PROJECT=steam app scrapy crawl forum

crawl_tags:  ## runs tags spider
	docker-compose exec -T -e SCRAPY_PROJECT=steam app scrapy crawl tags

crawl_developer:  ## runs developer spider
	docker-compose exec -T -e SCRAPY_PROJECT=steam app scrapy crawl developer

crawl_concurrent_players:  ## runs developer spider
	docker-compose exec -T -e SCRAPY_PROJECT=steam app scrapy crawl concurrent_players

crawl_dekanta:  ## runs dekanta spider
	docker-compose exec -T -e SCRAPY_PROJECT=whisky app scrapy crawl dekanta

crawl_grand:  ## runs grand spider
	docker-compose exec -T -e SCRAPY_PROJECT=whisky app scrapy crawl grand

crawl_yahoo:  ## runs yahoo spider
	docker-compose exec -T -e SCRAPY_PROJECT=whisky app scrapy crawl yahoo

crawl_whisky: crawl_dekanta crawl_grand crawl_yahoo
	@echo "done"

##@ Utilities

clean:  ## removes .pyc files
	@find . -type f -name '*.pyc' -exec rm {} +

mysql:  ## connects to local mysql cli
	docker-compose exec mysql mysql -ppassword --default-character-set=utf8 scraping

test: test_slick test_whisky test_steam ## runs all tests

test_slick:  ## runs slick tests
	python -m pytest test/slick/*

test_whisky:  ## runs whisky tests
	python -m pytest test/whisky/*

test_steam:  ## runs steam tests
	python -m pytest test/steam/*

mysqldump:  ## dumps local db
	mysqldump -d --host=127.0.0.1 --user=root --password=password scraping > dump.sql

publish: build  ## pushes to AWS
	@./publish.sh
