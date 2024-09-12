import os
import glob
import asyncio
import argparse
from itertools import cycle

from telethon import TelegramClient
from better_proxy import Proxy
from bot.core.registrator import register_sessions

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper

global tg_clients

start_text = """

<y>███╗   ███╗ █████╗      ██╗ ██████╗ ██████╗ ██████╗  ██████╗ ████████╗
████╗ ████║██╔══██╗     ██║██╔═══██╗██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝
██╔████╔██║███████║     ██║██║   ██║██████╔╝██████╔╝██║   ██║   ██║   
██║╚██╔╝██║██╔══██║██   ██║██║   ██║██╔══██╗██╔══██╗██║   ██║   ██║   
██║ ╚═╝ ██║██║  ██║╚█████╔╝╚██████╔╝██║  ██║██████╔╝╚██████╔╝   ██║   
╚═╝     ╚═╝╚═╝  ╚═╝ ╚════╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝   </y>

Select an action:

    1. Run clicker
    2. Create session
"""

def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_tg_clients() -> list[TelegramClient]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        TelegramClient(
            f'sessions/{session_name}',
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            system_version='Windows 11'
        )
        for session_name in session_names
    ]

    return tg_clients

async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")

    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")

    action = parser.parse_args().action

    if not action:
        logger.info(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2"]:
                logger.warning("Action must be 1 or 2")
            else:
                action = int(action)
                break

    if action == 1:
        tg_clients = await get_tg_clients()
        await run_tasks(tg_clients=tg_clients)

    elif action == 2:
        await register_sessions()




async def run_tasks(tg_clients: list[TelegramClient]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
            )
        )
        for tg_client in tg_clients
    ]

    await asyncio.gather(*tasks)
