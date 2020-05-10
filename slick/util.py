import importlib
import inspect

from slick import model, item

import scrapy


def _iter_classes(module, subclass):

	mods = importlib.import_module(module)

	for attr_name in dir(mods):
		attr = getattr(mods, attr_name)
		if inspect.isclass(attr) and issubclass(attr, subclass):
			yield attr


def get_model(name, model_name):
	for m in get_models(name):
		if m.__name__ == model_name:
			return m
	return None


def get_spiders(name):
	module = f"{name}.spiders"
	return [e for e in _iter_classes(module, scrapy.Spider)]


def get_models(name):
	module = f"{name}.models"
	return [e for e in _iter_classes(module, model.BaseModel)]


def get_items(name):
	module = f"{name}.items"
	return [e for e in _iter_classes(module, item.BaseItem)]
