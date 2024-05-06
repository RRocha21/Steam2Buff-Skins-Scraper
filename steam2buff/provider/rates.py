import re
import aiohttp

class Rates:
    base_url = 'http://data.fixer.io/api/latest?access_key=df5f93341f4086aef25b21643c18e212'

    csrf_pattern = re.compile(r'name="csrf_token"\s*content="(.+?)"')

    def __init__(self, request_interval):
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get_exchanges_rates_from_api(self):
        async with self.session.get(self.base_url) as response:
            try:
                response.raise_for_status()
                data = await response.json()
                return data['rates']
            except Exception as e:
                return None
    
    async def get_correct_price(self, currency_rates, base_currency, amount):
        for currency, rate in currency_rates.items():
            if base_currency == currency:
                return amount / rate
        return None