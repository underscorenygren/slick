import pickle
import os
import datetime
import json

import logging

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

SECRET_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def parse_creds(token_file=TOKEN_FILE, **kwargs):
	creds = None

	if os.path.exists(token_file):
		with open(token_file, 'rb') as f:
			creds = pickle.load(f)

	if not creds or not creds.valid:
		if creds and creds.expired and creds.refresh_token:
			creds.refresh(Request())
		else:
			flow = InstalledAppFlow.from_client_secrets_file(SECRET_FILE, SCOPES)
			creds = flow.run_local_server(port=0)
			with open(token_file, 'wb') as f:
				pickle.dump(creds, f)

	return creds


def write_data(spreadsheet_id, data, title=None, creds=None, **kwargs):
	creds = creds if creds is not None else parse_creds(**kwargs)
	service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

	title = title if title is not None else str(datetime.datetime.utcnow())

	# Call the Sheets API
	sheets = service.spreadsheets()
	requests = [
			{"addSheet": {
				"properties": {
					"title": title,
					"index": 0,
				}}}]

	body = {"requests": requests}

	res = sheets.batchUpdate(
			spreadsheetId=spreadsheet_id,
			body=body).execute()

	logger.info('Added sheet', str(res))

	range_ = f'{title}!A1:ZZZ1000000'
	value_input_option = 'USER_ENTERED'
	# I don't know how to pass a custom serializer
	# to google, so we'll do it jankily with a custom serialization/deseralization
	dateformat = json.dumps(data, default=lambda x: x.isoformat())
	body = {"values": json.loads(dateformat)}

	res = sheets.values()\
			.update(spreadsheetId=spreadsheet_id,
					range=range_,
					valueInputOption=value_input_option,
					body=body)\
			.execute()

	logger.info("added values", str(res))


if __name__ == "__main__":
	handler = logging.StreamHandler()
	logger.addHandler(handler)

	creds = parse_creds()
	sheet_id = '1rYKqYA67MpM2nY0T6pCTzDea6vM9fX1GJT3Iv3Ono14'
	data = [('Col 1', 'Col 2'), ("column one", "column two")]
	write_data(sheet_id, data, creds=creds)
