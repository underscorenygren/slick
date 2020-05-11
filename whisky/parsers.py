import datetime
import re


def regex_proc(reg, txt, postproc=None):
	found = re.search(reg, txt, flags=re.IGNORECASE)
	if found:
		target = found.group(1)
		return postproc(target) if postproc else target
	return None


def _liter_pp(v):
	return _tofloat(v) * 1000


def _cl_pp(v):
	return _tofloat(v) * 10


def _tofloat(v):
	return float(v)


def size(txt):
	regexs = [
		(r'(\d+)(:?\s+)?ml', _tofloat),
		(r'(\d+)(:?\s+)?cl', _cl_pp),
		(r'(\d+\.\d)+(:?\s+)?litre', _liter_pp),
		(r'([\.\d])+(:?\s+)?litre', _liter_pp),
	]
	for r, pp in regexs:
		res = regex_proc(r, txt, postproc=pp)
		if res is not None:
			return res
	return None


def abv(txt):
	regexs = [
		(r'(\d+\.\d)+%', _tofloat),
		(r'(\d+)%', _tofloat),
		(r'(\d+\.\d)+', _tofloat),
	]
	for r, pp in regexs:
		res = regex_proc(r, txt, postproc=pp)
		if res is not None:
			return res
	return None


def cask_no(txt):
	regexs = [
		(r'Cask\s+?#([-\d]+)', None),
		(r'Cask\s+No\.?#?([-\d]+)', None),
		(r'#([-\d]+)', None),
	]
	for r, pp in regexs:
		res = regex_proc(r, txt, postproc=pp)
		if res is not None:
			return res
	return None


def make_distillery_parser(distilleries):
	processed = [
			re.sub(r'\(\w+\)', '', dist).strip() for dist in distilleries]

	def distillery_parser(txt):
		for dist in processed:
			if txt.find(dist) != -1:
				return dist
		return None

	return distillery_parser


def _make_check_year(nowtime):
	def check_year(val):
		year = int(val)
		if 1800 <= year <= nowtime.year:
			return year
		return None
	return check_year


def age(txt, nowtime=None):
	nowtime = nowtime or datetime.datetime.utcnow()
	regexs = [
		(r'(\d{1,3})\s+Years?\s+Old', lambda v: int(v)),
		(r'(\d{1,3})\s+Years', lambda v: int(v)),
	]
	for r, pp in regexs:
		res = regex_proc(r, txt, postproc=pp)
		if res is not None:
			return res
	return None


def _to_1900(v):
	return 1900 + int(v)


def vintage(txt, nowtime=None):
	nowtime = nowtime or datetime.datetime.utcnow()
	regexs = [
		(r"(?:'|’)(\d{2})", _to_1900),
		(r'(\d{4})', _make_check_year(nowtime)),
	]
	for r, pp in regexs:
		res = regex_proc(r, txt, postproc=pp)
		if res is not None:
			return res
	return None


def currency(txt):
	if 'usd' in txt.lower() or '$' in txt:
		return 'USD'
	if u'円' in txt or u'¥' in txt:
		return 'JPY'


def take_first_nonempty(fn):
	def _inner(vals):
		for val in vals:
			res = fn(val)
			if res:
				return res
	return _inner
