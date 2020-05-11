# -*- coding: utf-8 -*-

BOT_NAME = 'whisky'

SPIDER_MODULES = ['whisky.spiders']
NEWSPIDER_MODULE = 'whisky.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
		'slick.middlewares.TransactionRecoverMiddleware': 300,
}

# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
		'slick.middlewares.MetricsDownloaderMiddleware': 543,
}

# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
		'whisky.pipeline.WhiskyItemPipeline': 200,
		'slick.pipeline.DBPipeline': 300,
}

# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
	'slick.extensions.PublishMetricsExtension': 300,
}

LOG_LEVEL = "INFO"
PUBLISHMETRICS_INTERVAL = 60
