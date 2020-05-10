"""
@package env

stores all our environment variables.
The are read once on module load, which
should happen at first import.
"""
import os


def _env(key, default=None):
	"""Returns the environment values for key, trimmed of quotes. default
	will be return if env value is Falsy."""
	env_val = os.environ.get(key)
	if env_val:
		env_val = env_val.strip('"')
	else:
		env_val = default
	return env_val


def _bool(var_name):
	"""gets env variable as bool"""
	return True if _env(var_name) else False


def _int(var_name, default=0):
	"""gets a value as int"""
	e = _env(var_name)
	return int(e) if e else default


def get(key, **kwargs):
	"""gets an environment variable by name,
	used for dynamically generated env variables, which
	are few and far between.

	default= provides default if key is not found.
	"""

	return _env(key, **kwargs)


def _mkattr(fn, key, default):
	"""wraps function in a lambda, so calling
	it refetches values"""
	return lambda: fn(key, default)


_attributes = {
	"mysql_host": _mkattr(_env, "MYSQL_HOST", "localhost"),
	"mysql_user": _mkattr(_env, "MYSQL_USER", 'root'),
	"mysql_port": _mkattr(_int, "MYSQL_PORT", 3306),
	"mysql_db": _mkattr(_env, "MYSQL_DB", 'scraping'),
	"mysql_password": _mkattr(_env, 'MYSQL_PASSWORD', 'password'),
	"mysql_charset": _mkattr(_env, 'MYSQL_CHARSET', 'utf8mb4'),
	"forum_search": _mkattr(_env, 'FORUM_SEARCH', 'parsec'),
}

"""use this attribute array to assign attributes
to make the refetcheable"""

def __getattr__(name):
	"""uses attributes array to actual fetch env variables"""
	fn = _attributes.get(name)
	if not fn:
		raise AttributeError(f"env param {name} not registered")
	return fn()
