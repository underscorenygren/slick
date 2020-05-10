from slick import cli

import locale

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

if __name__ == "__main__":
	parser = cli.ArgumentParser(name="steam")
	parser.run()
