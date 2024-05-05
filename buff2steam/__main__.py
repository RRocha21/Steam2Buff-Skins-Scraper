import asyncio
import decimal
from datetime import datetime

from buff2steam import config, logger
from buff2steam.provider.buff import Buff
from buff2steam.provider.steam import Steam
from buff2steam.provider.rates import Rates
from buff2steam.provider.postgres import Postgres

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
    
    total_page = 1000
    
    loop_random = random.random()
    
    for each_page in range(1, total_page + 1):
        random_sleep = random.randint(20, 40)
        await asyncio.sleep(random_sleep)
        if loop_random < 0.8:  
            items = await buff.get_items(1)
            logger.info(f'page: 1 / {total_page}...')
        else:
            items = await buff.get_items(each_page)
            logger.info(f'page: {each_page} / {total_page}...')
            
        start_time = time.time()

        for item in items:
            if item['id'] in visited:
                continue
            
            market_hash_name = item['market_hash_name']
            
            if 'Souvenir' in market_hash_name:
                continue
            
            buff_min_price = int(decimal.Decimal(item['sell_min_price']) * 100)
            buff_says_steam_price = int(decimal.Decimal(item['goods_info']['steam_price_cny']) * 100)

            if not config['main']['max_price'] > buff_min_price > config['main']['min_price']:
                continue

            buff_says_ratio = (buff_says_steam_price * (1 - steam.fee_rate)) / buff_min_price if buff_says_steam_price else 1
            accept_buff_threshold = config['main']['accept_buff_threshold']
            if buff_says_ratio < accept_buff_threshold:
                continue
            
            if 'Souvenir' in market_hash_name or 'SOUVENIR' in market_hash_name or 'souvenir' in market_hash_name:
                continue
            
            item_nameid = await postgres.check_item_nameid(market_hash_name)
            
            if not item_nameid:
                item_nameid = await steam.get_item_nameid(market_hash_name)
                await postgres.insert_item_nameid(item_nameid, market_hash_name)
            
            orders_data = await steam.orders_data(item_nameid)
            
            if orders_data is None:
                logger.info(f'Blocked by the steam api')
                raise SomeCustomException("Blocked by the steam API, restarting worker")
            else:
                b_o_ratio = (orders_data['highest_buy_order'] * (1 - steam.fee_rate)) / buff_min_price 
                b_o_ratio_threshold = config['main']['accept_buy_order_threshold']

                if b_o_ratio > b_o_ratio_threshold:
                    
                    correct_price = await rates.get_correct_price(exchange_rates, 'CNY', orders_data['highest_buy_order']/100)
                    correct_buff_price = await rates.get_correct_price(exchange_rates, 'CNY', buff_min_price/100)

                    item_to_psql = {
                        'id': item['id'],
                        'name': item['market_hash_name'],
                        'buff_min_price': buff_min_price/100,
                        'b_o_ratio': b_o_ratio,
                        'steamUrl': item["steam_market_url"],
                        'buffUrl': "https://buff.163.com/goods/" + str(item["id"]),
                        'updatedAt': datetime.now(),
                        'steam_price_cny': orders_data['highest_buy_order']/100,
                        'steam_price_eur': correct_price,
                        'buff_min_price_eur': correct_buff_price,
                    }

                    await postgres.insert_one(item_to_psql)
                
            visited.add(item['id'])
        end_time = time.time()
        logger.info(f'Page {each_page} took {end_time - start_time} seconds') 


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
