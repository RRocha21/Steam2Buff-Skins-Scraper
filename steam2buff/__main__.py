import asyncio
import decimal
from datetime import datetime

from steam2buff import config, logger
from steam2buff.provider.buff import Buff
from steam2buff.provider.steam import Steam
from steam2buff.provider.rates import Rates
from steam2buff.provider.postgres import Postgres

import random

import json

import time

visited = set()

async def reset_visited():
    global visited
    while True:
        await asyncio.sleep(300)  # 300 seconds = 5 minutes
        visited.clear()

async def main_loop(buff, steam, rates, postgres):
    global visited
    logger.info('Starting main loop...')
    await steam.get_proxy_list()
    
    psql_exchange_rates = await postgres.find_exchange_rate()

    exchange_rates_json = psql_exchange_rates.get('rates')  # Extracting exchange rates dictionary
    last_updated_str = psql_exchange_rates.get('updatedat')        # Extracting last updated timestamp
    last_updated = datetime.strptime(last_updated_str, '%Y-%m-%dT%H:%M:%S.%f')
    # Converting exchange rates dictionary to JSON string
    # Parsing exchange rates JSON string back to dictionary
    exchange_rates = json.loads(exchange_rates_json)
    
    if (datetime.now() - last_updated).total_seconds() > 43200:
        new_exchange_rates = await rates.get_exchanges_rates_from_api()
        psql_rate = {
            'id': 1,
            'rates': new_exchange_rates,
            'updatedAt': datetime.now(),
        }
        await postgres.update_rates(psql_rate)   
        exchange_rates = new_exchange_rates 
    
    
    loop_size = 100
    
    for i in range(0, loop_size):
        data = await postgres.fetch_steam_2_search()

        for item in data:
            # Fetch min price from Steam
            steam_price = await steam.get_min_price(item['market_hash_name'])
            
            if steam_price is None:
                continue
            
            # Fetch min price from Buff starting on the max float
            
            # buff_min_price = await buff.get_min_price(item['market_hash_name'], steam_price)
            
            # if buff_min_price is None:
            #     continue
            
            # # Calculate profit in percentage
            # profit = (buff_min_price - steam_price) / steam_price * 100
            
            # # Check if the item is profitable or until 10% loss
            # if profit >= 10:
            #     if item['market_hash_name'] not in visited:
            #         visited.add(item['market_hash_name'])
                    
            #         # Insert item into PostgreSQL
            #         await postgres.insert_steam_2_buff({
            #             'market_hash_name': item['market_hash_name'],
            #             'steam_price': steam_price,
            #             'buff_min_price': buff_min_price,
            #             'profit': profit
            #         })
            #         logger.info(f'Item {item["market_hash_name"]} is profitable: {profit:.2f}%')
            #     else:
            #         logger.info(f'Item {item["market_hash_name"]} is already visited')
            # else:
            #     logger.info(f'Item {item["market_hash_name"]} is not profitable: {profit:.2f}%')


async def main():
    try:
        while True:
            
            cookie_list = []
            
            with open('buff_accounts.txt', 'r') as file:
                for line in file:
                    session, remember_me = line.strip().split(',')

                    cookie_list.append((session, remember_me))

                    
            random_cookie = random.choice(cookie_list)
            selected_session, selected_remember_me = random_cookie
            
            config['buff']['requests_kwargs']['headers']['Cookie'] = f'session={selected_session};remember_me={selected_remember_me}'
            
            reset_task = asyncio.create_task(reset_visited())
            
            async with Buff(
                game=config['main']['game'],
                game_appid=config['main']['game_appid'],
                request_interval=config['buff']['request_interval'],
                request_kwargs=config['buff']['requests_kwargs'],
            ) as buff, Steam(
                game_appid=config['main']['game_appid'],
                request_interval=config['steam']['request_interval'],
            ) as steam, Rates(
                request_interval = 10,
            ) as rates, Postgres(
                request_interval = 10,
            ) as postgres:
                await main_loop(buff, steam, rates, postgres)
    except KeyboardInterrupt:
        exit('Bye~')


if __name__ == '__main__':
    asyncio.run(main())
