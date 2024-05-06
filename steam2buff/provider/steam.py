import asyncio
import re

import json

import random
from datetime import datetime, timedelta

import aiohttp
from aiohttp_socks import ProxyConnector

import urllib.parse

import decimal
from steam2buff import logger

def get_currency_from_id(currency_id):
    # Remove the first 2 characters from currency_id
    cleaned_currency_id = currency_id - 2000

    currency_mapping = {
        '1': 'USD',
        '2': 'GBP',
        '3': 'EUR',
        '4': 'CHF',
        '5': 'RUB',
        '6': 'PLN',
        '7': 'BRL',
        '8': 'JPY',
        '9': 'NOK',
        '10': 'IDR',
        '11': 'MYR',
        '12': 'PHP',
        '13': 'SGD',
        '14': 'THB',
        '15': 'VND',
        '16': 'KRW',
        '17': 'TRY',
        '18': 'UAH',
        '19': 'MXN',
        '20': 'CAD',
        '21': 'AUD',
        '22': 'NZD',
        '23': 'CNY',
        '24': 'INR',
        '25': 'CLP',
        '26': 'PEN',
        '27': 'COP',
        '28': 'ZAR',
        '29': 'HKD',
        '30': 'TWD',
        '31': 'SAR',
        '32': 'AED',
        '33': 'SEK',
        '34': 'ARS',
        '35': 'ILS',
        '36': 'BYN',
        '37': 'KZT',
        '38': 'KWD',
        '39': 'QAR',
        '40': 'CRC',
        '41': 'UYU',
        '42': 'BGN',
        '43': 'HRK',
        '44': 'CZK',
        '45': 'DKK',
        '46': 'HUF',
        '47': 'RON',
    }

    # Return the corresponding currency or 'Unknown' if not found
    return currency_mapping.get(str(cleaned_currency_id), 'Unknown')

last_subnet = ""

dead_https_proxies = {}
proxy_https_list = []

dead_socks4_proxies = {}
proxy_socks4_list = []

dead_socks5_proxies = {}
proxy_socks5_list = []

def get_https_proxy():
    global last_subnet, dead_https_proxies, proxy_https_list
    while True:
        ip = random.choice(proxy_https_list)
        ip_subnet = ip.split('.')[2]
        if ip_subnet == last_subnet:
            continue
        if ip in dead_https_proxies:
            if dead_https_proxies[ip] - datetime.utcnow() > timedelta(seconds=600):
                #proxy has not recovered yet - skip
                continue
            else:
                # proxy has recovered - set it free!
                del dead_https_proxies[ip]
        last_subnet = ip_subnet
        return ip
    
def get_socks4_proxy():
    global last_subnet, dead_socks4_proxies, proxy_socks4_list
    while True:
        ip = random.choice(proxy_socks4_list)
        ip_subnet = ip.split('.')[2]
        if ip_subnet == last_subnet:
            continue
        if ip in dead_socks4_proxies:
            if dead_socks4_proxies[ip] - datetime.utcnow() > timedelta(seconds=600):
                #proxy has not recovered yet - skip
                continue
            else:
                # proxy has recovered - set it free!
                del dead_socks4_proxies[ip]
        last_subnet = ip_subnet
        return ip
    
def get_socks5_proxy():
    global last_subnet, dead_socks5_proxies, proxy_socks5_list
    while True:
        ip = random.choice(proxy_socks5_list)
        ip_subnet = ip.split('.')[2]
        if ip_subnet == last_subnet:
            continue
        if ip in dead_socks5_proxies:
            if dead_socks5_proxies[ip] - datetime.utcnow() > timedelta(seconds=600):
                #proxy has not recovered yet - skip
                continue
            else:
                # proxy has recovered - set it free!
                del dead_socks5_proxies[ip]
        last_subnet = ip_subnet
        return ip
class Steam:
    base_url = 'https://steamcommunity.com'
    fee_rate = 0.13
    web_sell = '/market/sellitem'
    web_inventory = '/inventory/{steam_id}/{game_appid}/{context_id}'
    web_listings = '/market/listings/{game_appid}/{market_hash_name}'
    web_item_orders_histogram = '/market/itemordershistogram'
    web_search = '/market/search/render'

    item_nameid_pattern = re.compile(r'Market_LoadOrderSpread\(\s*(\d+)\s*\)')
    currency_pattern = re.compile(r'[^\d.]')

    def __init__(
            self, game_appid='',
            request_interval=40,
    ):
        self.request_interval = request_interval
        self.game_appid = game_appid
        self.web_listings = self.web_listings.replace('{game_appid}', game_appid)
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def get_proxy_list(self):
        # Read the HTTPS proxy list from the TXT file
        with open('./steam_proxy_http_list.txt', 'r') as file:
            proxy_https_list_data = file.readlines()

        duplicate_https_ips = set()
        unique_https_ips = set()

        for ip in proxy_https_list_data:
            if ip in unique_https_ips:
                duplicate_https_ips.add(ip)
            else:
                unique_https_ips.add(ip)

        # Assuming each line in the text file contains an HTTPS proxy
        for proxy in unique_https_ips:
            formatted_proxy = f'http://{proxy.strip()}'
            proxy_https_list.append(formatted_proxy)

        # Read the SOCKS4 proxy list from the TXT file
        with open('./steam_proxy_socks4_list.txt', 'r') as file:
            proxy_socks4_list_data = file.readlines()

        duplicate_socks4_ips = set()
        unique_socks4_ips = set()

        for ip in proxy_socks4_list_data:
            if ip in unique_socks4_ips:
                duplicate_socks4_ips.add(ip)
            else:
                unique_socks4_ips.add(ip)

        # Assuming each line in the text file contains a SOCKS4 proxy
        for proxy in unique_socks4_ips:
            formatted_proxy = f'socks4://{proxy.strip()}'
            proxy_socks4_list.append(formatted_proxy)

        # Read the SOCKS5 proxy list from the TXT file
        with open('./steam_proxy_socks5_list.txt', 'r') as file:
            proxy_socks5_list_data = file.readlines()

        duplicate_socks5_ips = set()
        unique_socks5_ips = set()

        for ip in proxy_socks5_list_data:
            if ip in unique_socks5_ips:
                duplicate_socks5_ips.add(ip)
            else:
                unique_socks5_ips.add(ip)

        # Assuming each line in the text file contains a SOCKS5 proxy
        for proxy in unique_socks5_ips:
            formatted_proxy = f'socks5://{proxy.strip()}'
            proxy_socks5_list.append(formatted_proxy)

        # Print the duplicate IPs

        if not proxy_https_list:
            raise NoProxiesAvailable()

        return True

    async def _request_with_https_proxy(self, *args, **kwargs):
        retries = 0

        url = self.base_url + urllib.parse.quote(args[1])
        while retries <= 100:
            proxy = get_https_proxy()
            try:
                connector = ProxyConnector.from_url(proxy)
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    try:
                        headers = kwargs.pop('headers', {})  # Extract headers from kwargs, if present
                        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
                        async with session.request(args[0], url, headers=headers, **kwargs) as response:
                            if response.status == 200: 
                                response_data = await response.text()
                                return response_data
                            else:
                                pass
                    except aiohttp.ClientError as ce:
                        pass
            except Exception as e:
                pass
                
            retries += 1
            dead_https_proxies[proxy] = datetime.utcnow()

        return None

    async def _request_with_socks4_proxy(self, *args, **kwargs):
        retries = 0
        url = self.base_url + urllib.parse.quote(args[1])
        while retries <= 100:
            proxy = get_socks4_proxy()
            try:
                connector = ProxyConnector.from_url(proxy)
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    try:
                        headers = kwargs.pop('headers', {})  # Extract headers from kwargs, if present
                        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
                        async with session.request(args[0], url, headers=headers, **kwargs) as response:
                            if response.status == 200: 
                                response_data = await response.text()
                                return response_data
                            else:
                                pass
                    except aiohttp.ClientError as ce:
                        pass
            except Exception as e:
                pass
                
            retries += 1
            dead_socks4_proxies[proxy] = datetime.utcnow()

        return None
    
    async def _request_with_socks5_proxy(self, *args, **kwargs):
        retries = 0
        url = self.base_url + urllib.parse.quote(args[1])
        while retries <= 100:
            proxy = get_socks5_proxy()
            try:
                connector = ProxyConnector.from_url(proxy)
                timeout = aiohttp.ClientTimeout(total=10)

                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                    try:
                        headers = kwargs.pop('headers', {})  # Extract headers from kwargs, if present
                        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
                        async with session.request(args[0], url, headers=headers, **kwargs) as response:
                            if response.status == 200: 
                                response_data = await response.text()
                                return response_data
                            else:
                                pass
                    except aiohttp.ClientError as ce:
                        pass
            except Exception as e:
                pass
                
            retries += 1
            dead_socks4_proxies[proxy] = datetime.utcnow()

        return None
    
    async def fetch_with_multiple_proxies(self, *args, **kwargs):
        proxy_functions = [
            self._request_with_https_proxy,    # 50% chance
            self._request_with_https_proxy,    # 50% chance
            self._request_with_https_proxy,    # 50% chance (to make it 50% total)
            self._request_with_socks4_proxy,   # 30% chance
            self._request_with_socks4_proxy,   # 30% chance (to make it 30% total)
            self._request_with_socks5_proxy,   # 20% chance
        ]

        # Choose a random proxy function
        selected_proxy_function = random.choice(proxy_functions)

        tasks = []
        for _ in range(25):
            task = asyncio.create_task(selected_proxy_function(*args, **kwargs))
            tasks.append(task)

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()

        # Get the result of the completed task
        for task in done:
            return task.result() if task.result() else None
    
    async def _web_listings(self, market_hash_name):
        return await self.fetch_with_multiple_proxies('GET', self.web_listings.format(market_hash_name=market_hash_name))
        
    async def _item_orders_histogram(self, item_nameid):        
        return await self.fetch_with_multiple_proxies('GET', self.web_item_orders_histogram, params={
            'language': 'english',
            'currency': 23,
            'item_nameid': item_nameid,
            'norender': 1,
            'country': 'UK',
            'two_factor': 0
        })

    async def _price_overview(self, market_hash_name):        
        return await self.fetch_with_multiple_proxies('GET', '/market/priceoverview', params={
            'appid': self.game_appid,
            'market_hash_name': market_hash_name,
            'currency': 23,
        })

    async def price_overview_data(self, market_hash_name):
        res = json.loads((await self._price_overview(market_hash_name)))
        
        if 'lowest_price' not in res:
            return None

        return {
            'price': int(decimal.Decimal(self.currency_pattern.sub('', res['lowest_price'])) * 100),
            'volume': int(res.get('volume', '0').replace(',', '')),
        }
        
    async def get_item_nameid(self, market_hash_name):
        res = await self._web_listings(market_hash_name)
        item_nameid = self.item_nameid_pattern.findall(res)
        
        if not item_nameid:
            return None
    
        return item_nameid[0]    

    async def orders_data(self, item_nameid):

        res = await self._item_orders_histogram(item_nameid)
        
        if not res:
            return None
        
        orders_data = json.loads(res)
        
        sell_order_count = str(orders_data['sell_order_count'])
        buy_order_count = str(orders_data['buy_order_count'])

        return {
            'sell_order_count': int(sell_order_count.replace(',', '')),
            'buy_order_count': int(buy_order_count.replace(',', '')),
            'lowest_sell_order': int(orders_data['lowest_sell_order']),
            'highest_buy_order': int(orders_data['highest_buy_order']),   
        }
