import aiohttp
import json
from datetime import datetime
from buff2steam import logger

class Postgres:
    base_url = 'http://192.168.3.31:8000'

    def __init__(self, request_interval):
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def inspect_one(self, link):
        url = f'{self.base_url}?url={link}'
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                if 'iteminfo' in data:
                    return data['iteminfo']['floatvalue']
                return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    async def insert_one(self, document, max_points=25):
        try:
            id = int(document["id"])
            # Extract other fields from document
            name = document["name"]
            buff_min_price_not_rounded = document["buff_min_price"]
            buff_min_price = round(float(buff_min_price_not_rounded), 2)
            
            b_o_ratio_not_rounded = document["b_o_ratio"]
            b_o_ratio = round(float(b_o_ratio_not_rounded), 2)
            
            steamUrl = document["steamUrl"]
            buffUrl = document["buffUrl"]
            updatedAt = document["updatedAt"].strftime('%Y-%m-%dT%H:%M:%S.%f')
            
            steam_price_cny_not_rounded = document["steam_price_cny"]
            steam_price_eur_not_rounded = document["steam_price_eur"]
            buff_min_price_eur_not_rounded = document["buff_min_price_eur"]
            
            steam_price_cny = round(float(steam_price_cny_not_rounded), 2)
            steam_price_eur = round(float(steam_price_eur_not_rounded), 2)
            buff_min_price_eur = round(float(buff_min_price_eur_not_rounded), 2)
            
            url = f'{self.base_url}/buff2steam'

            async with self.session.post(url, params={
                'id': id,
                'name': name,
                'buff_min_price': buff_min_price,
                'b_o_ratio': b_o_ratio,
                'steamUrl': steamUrl,
                'buffUrl': buffUrl,
                'updatedAt': updatedAt,
                'steam_price_cny': steam_price_cny,
                'steam_price_eur': steam_price_eur,
                'buff_min_price_eur': buff_min_price_eur
            }) as response:
                response.raise_for_status()
        except Exception as e:
            logger.error(f'Failed to insert document into PostgreSQL: {e}')

    async def update_rates(self, document, max_points=50):
        try:
            id = document['id']
            rates = json.dumps(document['rates'])
            updatedAt = document["updatedAt"].strftime('%Y-%m-%dT%H:%M:%S.%f')  # Convert datetime to ISO 8601 formatted string

            url = f'{self.base_url}/exchange_rates'

            async with self.session.post(url, params = {
                'rates': rates,
                'updatedAt': updatedAt
            }) as response:
                response.raise_for_status()
            
        except Exception as e:
            print(f'Failed to insert document into PostgreSQL: {e}')
            
    async def find_exchange_rate(self):
        try:
            id = 1
            
            url = f'{self.base_url}/exchange_rates'
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return data[0]
        except Exception as e:
            print(f'Failed to find exchange rate in PostgreSQL: {e}')

    async def check_item_nameid(self, market_hash_name):
        try:
            url = f'{self.base_url}/item_nameid'
            async with self.session.get(url, params={'market_hash_name': market_hash_name}) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        return data[0]['item_nameid']
                    return None
                return None
        except Exception as e:
            logger.error(f'Failed to check item nameid: {e}')
            return None

    async def insert_item_nameid(self, item_nameid, market_hash_name):
        try:
            url = f'{self.base_url}/item_nameid'
            async with self.session.post(url, params={
                'market_hash_name': market_hash_name, 
                'item_nameid': item_nameid
            }) as response:
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f'Failed to insert item nameid: {e}')
