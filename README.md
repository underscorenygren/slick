# Slick

Slick is a webscraping framework based on [scrapy](https://docs.scrapy.org/en/latest/).

It adds an opinionaded structure on top of `scrapy` and `sqlalchemy`, to allow you to quickly
define and create models and corresponding items that are then easily queriable, joinable, 
and uploadable to backends such as _Google Sheets_.

This project also contains two example uses of Slick:
- `steam` scrapes steam and steamcharts for information about games.
- `whisky` crawls whisky sites for pricing information.

## TL;DR

See the makefile for common commands, view help by typing `make`.

To get started, install: `make install`, then run `make up`. This
will start the necessary background processes.\
Then, type `make crawl_forum` or `make crawl_tags` to start one of
the crawl spiders.

When you're done, `make down` will stop the system. It will persist the data to pick back up later.
If you want to remove the data, you will have to clear the persisted volume with `docker volume rm`.

## Installation

You must have a docker engine running, which you can [download here](https://docs.docker.com/v17.09/engine/installation/).

`make install` will build images and create tables

## Architectural Overview

### Docker

For ease and concistency, `slick` is written with Docker in mind. It ships with a defined
docker environment where scrapers are run, and uses `docker-compose` to run a local 
mysql instance where data is kept persistent between runs. 

This project assumes you are already familiar with docker and docker-compose, there's
no documentation for it outside the makefile.


### Scrapy

In scrapy, a crawl is defined as a _project_, which can include one or more _spiders_. Spiders
are subclasses of `scrapy.Spider`, and define urls and patterns for crawling sites. 

To create a new crawl project, use the scrapy command line tool:

`scrapy startproject [mycrawl]`

At the core of `scrapy` is _Items_, a glorified dictionary composed of named 
[fields](https://docs.scrapy.org/en/latest/topics/items.html#item-fields).
They are intended as a place to register how to find pieces of data on a page and how 
to clean them, using _xpaths_ or _css selectors_ (and a host of other getters/processors).\
For more information on items and item loaders, check the [scrapy docs for items](https://docs.scrapy.org/en/latest/topics/items.html).

Scrapy also has the concept of [middleware](https://docs.scrapy.org/en/latest/topics/spider-middleware.html).
Slick uses middleware such things as tracking processed urls and SQL transaction recovery.

Scrapy has a host of configuration options, configured in `settings.py` files. 
Note that this is where `scrapy` _middlewares_ and _pipelines_ are configured, so if you add new classes, be
sure to register them there.

### SQLAlchemy

`sqlalchemy` is a python-based SQL ORM from the `flask` project, and is a handy way to express
database tables using python classes. In the code, we refer to these as _Models_ to distinguish
them from `scrapy` _Items_.

### Slick

Slick is an opinionated framework that glues `scrapy` and `sqlalchemy` together. It uses 
`sqlalchemy` _Models_ to define both DB schema for storage and functions for automatically building
`scrapy` _Items_ from them and then querying and joining them without the need for redundant code.

### UrlCache

Many spiders use a SQL url cache. Urls are inserted in a pending state, and
marked as crawled when successfully parsed. This intended to help us restart crawls, but might be better done with
[scrapy jobs](https://docs.scrapy.org/en/latest/topics/jobs.html).

In the meantime, you might want to clear the url cache from time to time by running
`truncate url_cache;` inside mysql.

### Randomizing

Many crawls start with a list of urls. We tend to start off by shuffling these, to make sure we don't
get stuck on the same place. By default, crawls are depth first, which isn't always ideal. You can change
it using the [instructions here](https://docs.scrapy.org/en/latest/faq.html#does-scrapy-crawl-in-breadth-first-or-depth-first-order).

## Data Model

### Items vs Models

We use two concepts to handle data transitions throughout the systems. `Items` is for data scraped from a page,
`Models` is for data stored in SQL.

#### Models

Models are typed mysql models that uses `sqlalchemy` as an ORM. Each field on the DB model should correspond
to a piece of data that can be scraped from a page, as well as related pieces of data using foreign keys
and relationships. 

Fields in models are typed, which affects what kind of processing scrapy will do to them.

#### Items

In `slick`, you create items by using the `realize_item_class` function from the [model](slick/model.py) module:

```python
MyItemClass = model.realize_item_class("MyItemClass", MyModelClass)
```

This will create an item class that automatically wires all the model attributes as fields on the item, 
and allows you to look up instances in the db based on a (partially) filled item. 

To create item, you use the slick `BaseLoader`, located in [item](slick/item.py) module.

```python
def load_something(response):
  loader = item.BaseLoader(MyItemClass(), response=response)
  loader.add_css('property1', '.some-class-name')
  loader.add_xpath('property2', '//*[@id="some-xpath"]')
  return loader.load_item()
```

This will ensure your items is wired correctly.

## Slick Concepts

Like in `scrapy` a scraper is a collection of spiders nested under a module directory. 

In `slick`, you will find utility modules for the various scrapy concepts, named in the singular:
- `item` - defines base _Item_ and _ItemLoader_ classes you should inherit from.
- `model` - defines logic for mapping models to items, and various `sqlalchemy` utilities.
- `parser` - defines utility functions for parsing and casting data from crawls to python types.
- `pipeline` - defines DBPipeline, which you should use as the pipeline in your _scrapy_ `settings.py`
    which will handle translating items into their corresponding models and upserting them into the DB.
- `spider` - provides _mixins_ for use in the `scrapy.Spider` you define in your crawls.
- `util` - provides various utility functions, such as listing all registered models, items and spiders.

The suggested convention is that you lay out your project with items/models/etc separated by file
and module, and name them in the plural.

```bash

├── myscrape/
│   ├── __init__.py
│   ├── items.py
│   ├── models.py
│   ├── middlewares.py
│   ├── parsers.py
│   ├── settings.py
│   ├── spiders/
│   │   ├── __init__.py
│   │   ├── spiderone.py
│   │   ├── spidertwo.py
│ myscrape.py
```

### Realized Items

To make item building easy slick uses the class-building function `model.realize_item_class` to make items from models.\
Item classes using this function will have fields from all the models columns and relationships, with the exception
of primary and foreign keys. You should use this function to build all your item classes.

```python
import sqlalchemy
from slick import model

class MyModel(model.BaseModel):
  __tablename__ = "mymodel"

  id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
  field = sqlalchemy.Column(sqlalchemy.String(64))

MyItem = model.realize_item_class("MyItem", MyModel)

my_item = MyItem(field='some-field')
# field is now an attribute on MyItem
```

If you need to wire behavior on your item classes, use inheritence:

```python
class MySpecialItem(MyItem):

  def foo(self):
    return "bar"
```

### Loading Items

`slick` uses the `scrapy` concept of `ItemLoader` to create all items. A slick `BaseLoader`
is defined in the `model` module, and you should use this for loading of items when you scrape.
See more on _dependent models_ below.

### Mapping items to models / lookup_attributes

In order to map parsed items to models that have already been inserted into the db,
we need to define how to map an instantiated item to an instantiated model (pulled from the DB).
This is done through the `_lookup_attributes` property registered on the model class.\
This property takes a list of attributes names that map to columns registered on the model.
When looking up a model, `slick` will automatically create a sql query 
(a sqlalchemy `query.filter()` to be exact).
As of this writing, it will simpy `AND` all lookup attributes together, but this could easily be extended. 

```python
import sqlalchemy
from slick import model

class MyModel(model.BaseModel):
  __tablename__ = "mymodel"

  id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
  field = sqlalchemy.Column(sqlalchemy.String(64))

MyItem = model.realize_item_class("MyItem", MyModel)

# normally items are yielded during regular parsing with their fields filled in
my_item = MyItem(field="normally-looked-up-in-parsing")

# the get_from_item fn is used in the slick pipeline to do this lookup automatically
my_model = MyModel.get_from_item(my_item)
# None

inserted = model.upsert(MyModel, my_item)

my_model_again = MyModel.get_from_item(my_item)
# my_model_again == inserted
```

### Dependent models/items

In scraping, it's quite common that two pieces of data on different pages are related. For example,
if you're crawling recipes, you might want to store recipes in one table and authors in another. 
In sql, you could model this as a relation from recipes to authors using a foreign key relationship.
With `slick` you would just define the model with the relation as you would in `sqlalchemy`,
and instruct the item loader how to join the two using the `add_dependent` function:

```python
import sqlalchemy
from slick import model

class Recipe(model.BaseModel):
  __tablename__ = "recipe"
  _lookup_attributes = ('name', )
  id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
  name = sqlalchemy.Column(sqlalchemy.String(128), index=True)
  author_id = ForeignKey("game.id")

  author = relationship("Author")


class Author(model.BaseModel):
  __tablename__ = 'author'
  _lookup_attributes = ('name', )

  id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
	name = sqlalchemy.Column(sqlalchemy.String(128), index=True)

  recipe = relationship("Recipe")


RecipeItem = model.realize_item_class("RecipeItem", Recipe)
AuthorItem = model.realize_item_class("AuthorItem", Recipe)


def load_recipe(response):
  recipe_loader = model.BaseLoader(Recipe(), response=response)
  author_loader = model.BaseLoader(Author(), response=response)

  author_loader.add_css('name', '.author-name')
  recipe_loader.add_css('name', '.recipe-name')
  author_item = author_loader.load_item()
  recipe_loader.add_dependent('author', author_item)

  return recipe_loader.load_item()
```

This will instruct the _item_ to _model_ mapper to look up dependent models when it's constructing the new recipe model
from the recipe item.\
In this example case, it will look up an author model by the dependent `author` we registered, i.e. looking it up
by the parsed _name_ attribute (since that's what's registered as its _lookup_attributes_). If there's a match,
slick pipeline processing will map to the existing entry, otherwise it will create and insert a new object.
There's no need to parse or lookup `author_id` in the item loader or anywhere in the code.


### Placeholders

Sometimes you want to parse information from a page that you don't want to insert into the DB, 
perhaps used to correlate with other pieces of data on the system. You can register these _placeholder_
fields on a model by using the slick `model.Placeholder` class.

```python
import sqlalchemy
from slick import model

class PlaceholderModel(model.BaseModel):
	__tablename__ = 'placeholder'

	id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)

	placeholder = model.Placeholder()


PlaceholderItem = model.realize_item_class("PlaceholderItem", PlaceholderModel)


#placeholder field is registered on PlaceholderItem class
```


### CLI

`slick` ships with a command line tool creator, `ArgumentParser`, which you can use to create
easy command line tools for your scrapes. It's located in the `cli` module.

To use it, create a python file at the root of this project, instantiate and run it. I haven't
yet gotten python importing to a state where I can do this in the project directories themselves,
but that will be coming.

```python
#myscraper.py
from slick import cli

if __name__ == "__main__":
	parser = cli.ArgumentParser(name="myscraper")
	parser.run()
```

The `cli` ships with a handful of useful commands. You can interrogate it by using `--help`

In particular, you can export data straight to _Google Sheets_ by providing it with the `--sheets` parameter.

`python myscraper.py MyModel --sheets somelongsheetsidXYZ`

This will upload all objects found in MyModel to the sheet.

To get sheets authentication set up, follow the [Google setup guide](https://developers.google.com/sheets/api/quickstart/python)


## Testing

Tests aren't currently in docker, so you must have _python 3_ installed. Currently, the makefile
assumes the binary is called `python`, I use `pyenv` to manage this and encourage you to do the same.

Before you run them, install dependencies using `pip -r requirements.txt`.

Tests are defined in [test/](./test/).

## MySQL

Mysql runs in docker, but it exposes the port on the host machine. This means that you can
connect to it on your localhost. The password is in [docker-compose.yaml](./docker-compose.yaml).

When running your scrapers you can point them to a different database by configuring through
environment variables:
- MYSQL_HOST
- MYSQL_USER
- MYSQL_PORT
- MYSQL_DB
- MYSQL_PASSWORD
- MYSQL_CHARSET

## Interrogating Mysql Schema

This is a helpful shorthand for mysql commands you want to be familiar with.

`show databases`

shows which databases are available

`show tables`

lists what tables are available

`describe {table_name}`

shows a table schema

`show create table {table_name}`

shows the full structure of the table, including foreign key references and indexes.

`mysqldump --host={host} --user={user} --password={password} --no-data --skip-add-drop-table`

will print the entire sql structure of the DB, essentailly calling `show create table` for each table.
