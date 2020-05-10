"""running commands"""
import argparse
import logging
import os
import time

import sqlalchemy

import env
from slick import model, util
import lib
import sheets


logging.basicConfig()
logger = logging.getLogger(__name__)


def _create(name, drop=False):
	"""recreates all tables"""
	# we just need to import them, we don't need to refer to them
	util.get_models(name)
	engine = model.get_engine()

	while True:
		logger.info("dropping all")
		try:
			if drop:
				if env.mysql_host not in ['mysql', 'localhost', '127.0.0.']:
					raise Exception("cowardly refusing to recreate tables on non-local mysql instance")
				model.BaseModel.metadata.drop_all(engine)
				logger.info("recreating all")
			model.BaseModel.metadata.create_all(engine)
			logger.info("done")
			break
		except sqlalchemy.exc.OperationalError as e:
			if str(e).find('"Can\'t connect to MySQL server') > -1:
				logger.info("couldn't connect, waiting until available")
				time.sleep(1)
			else:
				raise e


def _as_dict(obj):
	return obj.as_dict()


def _mysql(model_class, formatter=lib.json_formatter, converter=_as_dict, printer=print, **kwargs):
	"""queries mysql"""
	with model.db_context() as db:
		printer(
			formatter(
				[converter(row) for row in db.query(model_class).all()]))


class SheetsPrinter(object):
	def __init__(self):
		self.buffered = []

	def __call__(self, data):
		if not data:
			return
		first = data[0]
		self.buffered.append(list(first.keys()))
		for row in data:
			self.buffered.append(list(row.values()))

	def write(self, spreadsheet_id):
		sheets.write_data(spreadsheet_id, self.buffered)


def create_readonly_user(args):
	"""creates a readonly user in the db"""
	password = args.password
	create_q = f"create user 'read-only'@'%' IDENTIFIED BY '{password}';"
	grant_q = "grant select on *.* TO 'read-only'@'%';"
	with model.db_context() as db:
		for q in [create_q, grant_q]:
			db.execute(q)


class ArgumentParser(argparse.ArgumentParser):
	"""wrapped argparse for slick-based scrapers,
	adds some conveniences"""
	def __init__(self, *args, name=None, **kwargs):
		"""wraps init"""
		super().__init__(*args, **kwargs)
		self.name = name
		self.argparse_subparsers = self.add_subparsers()
		self.registered_subparsers = []
		# even base parser has func set
		self.set_defaults(func=lambda x: self.print_help())

	def set_name(self, name):
		self.name = name

	def add_subparser(self, name, fn, **kwargs):
		subparser = self.argparse_subparsers.add_parser(name, **kwargs)
		subparser.set_defaults(func=fn)
		self.registered_subparsers.append(subparser)
		return subparser

	def add_argument_to_all(self, *args, **kwargs):
		for subparser in self.registered_subparsers:
			subparser.add_argument(*args, **kwargs)

	def create(self, args):
		"""creates db tables"""
		_create(self.name, drop=False)

	def recreate(self, args):
		"""recreates tables"""
		_create(self.name, drop=True)

	def query(self, args):
		"""parses args, queries mysql"""
		model_name = args.name
		model_class = util.get_model(self.name, model_name)
		if not model_class:
			raise ValueError(f"no {model_name} exists in {self.name}")

		if args.sheet:
			spreadsheet_id = args.sheet
			sheets_printer = SheetsPrinter()
			_mysql(model_class, formatter=lambda x: x, printer=sheets_printer)
			sheets_printer.write(spreadsheet_id)
		else:
			_mysql(model_class,
				formatter=lib.csv_formatter if args.csv else lib.json_formatter)

	def ls(self, args):
		p = print

		for fn in [util.get_spiders, util.get_models, util.get_items]:
			for e in fn(self.name):
				p(e)

	def run(self):
		parser = self
		parser.add_subparser("create", self.create, help="creates db models")
		parser.add_subparser("recreate", self.recreate, help="recreates db models")
		parser.add_subparser("ls", self.ls, help="lists info about scraper")

		subparser = parser.add_subparser("query", self.query, help="queries models by classname")
		subparser.add_argument('--name', type=str, help="the name of the model to query")
		subparser.add_argument('--desc', action="store_true", help="show list in desc order instead of asc")
		subparser.add_argument('--csv', action="store_true", help="writes in csv format instead of json")
		subparser.add_argument('--sheet', type=str, help="writes data to google spreadsheet")
		subparser.add_argument('--print', dest='p', action="store_true", help="prints sql query instead of results")

		do_create_readonly_user = parser.add_subparser('create_readonly_user', create_readonly_user, help="creates readonly user in db")
		do_create_readonly_user.add_argument('--password', type=str, help="the password for the user")

		parser.add_argument_to_all('--env-file', type=str, help="loads env vars from file")
		args = parser.parse_args()

		if args.env_file:
			_load_env_file(args.env_file)
			model.rebind()

		return args.func(args)


def _load_env_file(file_name):
	"""loads environment vars from files"""
	with open(file_name, 'r') as f:
		for line in f.readlines():
			(key, value) = line.strip().split('=')
			key = key.strip().strip('"')
			value = value.strip().strip('"')
			os.environ[key] = value
