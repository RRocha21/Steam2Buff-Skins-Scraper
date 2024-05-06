import asyncio
import decimal
from datetime import datetime

from steam2buff import config, logger
from steam2buff.provider.buff import Buff
from steam2buff.provider.steam import Steam
from steam2buff.provider.rates import Rates
from steam2buff.provider.postgres import Postgres
from steam2buff.provider.sheets import Sheets

import random

import json

import time

visited = set()

async def reset_visited():
    global visited
    while True:
        await asyncio.sleep(300)  # 300 seconds = 5 minutes
        visited.clear()

async def main_loop(buff, steam, rates, postgres, sheets):
    logger.info(f'Fetching data from Google Sheets...')
    sheet_data = await sheets.fetch_all()
    logger.info(f'Fetched {len(sheet_data)} items from Google Sheets')
    
    for item in sheet_data:
        await asyncio.sleep(0.1)
        logger.info(f'Fetching {item}')
        await postgres.insert_one_steam_2_search(item)



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
            ) as postgres, Sheets(
                credentials=config['sheets']['credentials'],
                sheet_id=config['sheets']['sheet_id'],
                sheet_name=config['sheets']['sheet_name'],
                file_name=config['sheets']['file_name'],
            ) as sheets:
                await main_loop(buff, steam, rates, postgres, sheets)
    except KeyboardInterrupt:
        exit('Bye~')


if __name__ == '__main__':
    asyncio.run(main())
