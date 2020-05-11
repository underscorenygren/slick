"""tests whisky"""
import datetime

from whisky import parsers

def test_size_parser():
	assert 180.0 == parsers.size("180ml")
	assert 180.0 == parsers.size("180 ml")
	assert 180.0 == parsers.size("180  ml")
	assert 1000.0 == parsers.size("1 litre")
	assert 1500.0 == parsers.size("1.5 litre")
	assert 180.0 == parsers.size("Nikka Single Malt Coffey Grain Whisky Woody & Mellow – 180ml")


def test_abv_parser():
	assert 40.0 == parsers.abv("40%")
	assert 58.8 == parsers.abv("58.8%")
	assert 58.8 == parsers.abv("Some Whisky at 58.8% alc")
	assert 49.7 == parsers.abv('<li>\n                            <strong>Strength (%):</strong> 49.7\n                    </li>')


def test_cask_no_parser():
	assert "8421" == parsers.cask_no("Single Cask #8421")
	assert "6355-04" == parsers.cask_no("2001 Exceptional Cask #6355-04 2019 Release")
	assert "14" == parsers.cask_no("#14")


def test_distillery_parser():
	test_distilleries = [
		"Ardtalnaig (Lochtayside)",
		"Argyll/Mackinnon's",
		"Argyll",
	]
	parser = parsers.make_distillery_parser(test_distilleries)
	assert "Argyll" == parser("Argyll 2010 Some Cask")
	assert "Ardtalnaig" == parser("Fine specimen of Ardtalnaig")
	assert "Argyll/Mackinnon's" == parser("2001 Argyll/Mackinnon's Exceptional Cask #6355-04 2019 Release")


def test_vintage_parser():
	t = datetime.datetime(year=2020, month=1, day=1)

	def parser(v):
		return parsers.vintage(v, nowtime=t)

	assert 1987 == parser("Suntory Special Reserve Whisky ’87 – Bird")
	assert 1977 == parser("Brora - 24 Year Old - 1977 Rare Malts")
	assert 2001 == parser("Macallan - 2001 Exceptional Cask #6355-04 2019 Release")


def test_age_parser():
	t = datetime.datetime(year=2020, month=1, day=1)

	def parser(v):
		return parsers.age(v, nowtime=t)

	assert 15 == parser("Macallan - 15 Year Old - Gran Reserva (2017)")
	assert 24 == parser("Brora - 24 Year Old - 1977 Rare Malts")
	assert 37 == parser("Brora - 37 Years Old - 2015 Release")
	assert 105 == parser("Pirate ship found 105 Years Old")
