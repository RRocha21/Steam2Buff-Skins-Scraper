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

from urllib.parse import unquote

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
            item_skin_name = item['skinname']
            item_buff_id = item['buffid']
            item_buff_url = item['buffurl']
            item_steam_url = item['steamurl']
            item_min_float = round(float(item['minfloat']),3)
            item_max_float = round(float(item['maxfloat']),3)
            item_status = item['status']
            
            
            
            # Fetch min price from Steam
            market_hash = unquote(item_steam_url.split("/")[-1])
            steam_overview = await steam.price_overview_data(market_hash)
            
            if steam_overview is None:
                continue
            
            # Give a 5% margin to the min price
            steam_min_price = steam_overview['price'] * 1.05
            # Fetch min price from Buff starting on the max float
            
            float_interval = 0.1
            if (item_max_float == 0.27):
                float_interval = 0.01
            else:
                float_interval = 0.005
            
            last_buff_price = None
            last_steam_price = None
            last_max_float = None
            
            retries_with_same_price = 0

            
            for x in range(int(item_min_float*1000) + int(float_interval*1000), int(item_max_float*1000), int(float_interval*1000)):
                current_float = x/1000
                buff_min_price = await buff.get_min_price(item_buff_id, current_float)
                
                if buff_min_price is None:
                    continue
                
                
                max_loss = 0.95 # 10% loss
                
                loss_percent = (float(buff_min_price) / float(steam_min_price))
                if loss_percent > max_loss:
                    if (last_buff_price == buff_min_price):
                        retries_with_same_price += 1
                    else:
                        retries_with_same_price = 0
                        last_buff_price = buff_min_price
                        last_steam_price = steam_min_price
                        last_max_float = current_float
                        
                    if retries_with_same_price > 2:
                        break;

                    continue
                else:
                    break
            
            if last_buff_price is not None and last_steam_price is not None and last_max_float is not None:
                
                # Insert into PostgreSQL
                psql_steam_2_buff = {
                    'link': item_steam_url,
                    'max_float': last_max_float,
                    'max_price': last_steam_price,
                    'status': 'True',
                    'buff_id': item_buff_id,
                }
                await postgres.insert_into_steam_links(psql_steam_2_buff)
                    
                logger.info(f'Inserted {item_skin_name} into PostgreSQL')
            else:
                await postgres.update_steam_2_search(item_buff_id, 'False')


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
