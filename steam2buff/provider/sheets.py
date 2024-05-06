from steam2buff import logger
from steam2buff.exceptions import BuffError

import gspread
from oauth2client.service_account import ServiceAccountCredentials

class Sheets:

    def __init__(self, credentials=None, file_name=None, sheet_id=None, sheet_name=None):
        if credentials is None and file is None and sheet_id is None and sheet_name is None:
            request_kwargs = {}


        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials_account = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)

        try:
            client = gspread.authorize(credentials_account)
            self.sheet_id = sheet_id
            self.sheet_name = sheet_name
            self.file_name = file_name
            self.client = client
        except:
            logger.error('Failed to connect to Google Sheets!')
            exit(1)


    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.error('Exit Sheets')

    async def fetch_one(self, total_rows):
        try:
            logger.debug(f'Fetching data from Google Sheets...')
            logger.debug(f'File Name: {self.file_name}')
            logger.debug(f'Sheet Name: {self.sheet_name}')

            sheet = self.client.open(self.file_name).worksheet(self.sheet_name)

            data = sheet.get_all_values()
            limited_data = data[1:total_rows]

            new_data = []


            for row in limited_data:
                row_data = {
                    'link': row[1],
                    'buff_id': row[2],
                    'max_float': float(row[3].replace(',', '.')),
                    'max_price': float(row[4].replace(',', '.')),
                    'status': row[5]
                }

                new_data.append(row_data)
            return new_data

        except Exception as e:
            logger.error(f'Failed to fetch data from Google Sheets: {e}')
            raise BuffError('Failed to fetch data from Google Sheets!')

    async def fetch_total_rows(self):
        try:
            logger.debug(f'Fetching total rows from Google Sheets...')

            sheet = self.client.open(self.file_name).worksheet(self.sheet_name)

            data = sheet.get_all_values()
            row_index = 0

            for row in data:
                if not (row[1] and row[2] and row[3] and row[4] and row[5]):
                    break;
                row_index += 1
            logger.debug(f'Fetched total rows from Google Sheets: {row_index}')
            return row_index
        except Exception as e:
            logger.error(f'Failed to fetch total rows from Google Sheets: {e}')
            raise BuffError('Failed to fetch total rows from Google Sheets!')
        
    async def fetch_all(self):
        try:
            logger.debug(f'Fetching data from Google Sheets...')
            logger.debug(f'File Name: {self.file_name}')
            logger.debug(f'Sheet Name: {self.sheet_name}')

            sheet = self.client.open(self.file_name).worksheet(self.sheet_name)

            data = sheet.get_all_values()
            limited_data = data[1:4898]

            new_data = []


            for row in limited_data:
                row_data = {
                    'buffUrl': row[1],
                    'buffId': row[2],
                    'skinName': row[3],
                    'steamUrl': row[5],
                    'maxFloat': row[6].replace(',', '.')
                }
                logger.info(f'Row Data: {row_data}')

                new_data.append(row_data)
            return new_data

        except Exception as e:
            logger.error(f'Failed to fetch data from Google Sheets: {e}')
            raise BuffError('Failed to fetch data from Google Sheets!')