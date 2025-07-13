import discord
import asyncio
import sqlite3

from discord.ext import commands

# Local imports
from cogs import get_cog_modules
from bot_config.config import *


class MonkaMind(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True

        super().__init__(
            command_prefix="!", 
            intents=intents
        )

        self.config_db: sqlite3.Connection = None
        self.token: str = None
        self.version: str = '2.0.0'
        self.pin_channel_id: int = 0
        self.geopy_username: str = None
        self.nasa_api_key: str = None

    async def setup_hook(self):
        self.config_db = open_config_db_connection('./bot_config/config.db')
        if not self.config_db:
            raise Exception('Failed to create config connection')

        # Get bot token from config database
        result = execute_query(
            config_connection=self.config_db,
            query='SELECT CONFIG_VALUE FROM CONFIG WHERE CONFIG_KEY = ?',
            params=('TOKEN',),
            fetch_one=True
        )

        if result and result['CONFIG_VALUE']:
            self.token = result['CONFIG_VALUE'] 
        else:
           raise Exception('Failed to fetch bot token from config database') 
        
        # Get bot pinned messages channel ID from config database
        result = execute_query(
            config_connection=self.config_db,
            query='SELECT CONFIG_VALUE FROM CONFIG WHERE CONFIG_KEY = ?',
            params=('PIN_CHANNEL_ID',),
            fetch_one=True
        )

        if result and result['CONFIG_VALUE']:
            self.pin_channel_id = result['CONFIG_VALUE'] 
        else:
           raise Exception('Failed to fetch pinned messages channel ID from config database') 
        
        # Get the geo-py username from the config database
        result = execute_query(
            config_connection=self.config_db,
            query='SELECT CONFIG_VALUE FROM CONFIG WHERE CONFIG_KEY = ?',
            params=('GEOPY_USERNAME',),
            fetch_one=True
        )

        if result and result['CONFIG_VALUE']:
            self.geopy_username = result['CONFIG_VALUE'] 
        else:
           raise Exception('Failed to fetch geo-py username from config')

        # Get the nasa api key from the config database
        result = execute_query(
            config_connection=self.config_db,
            query='SELECT CONFIG_VALUE FROM CONFIG WHERE CONFIG_KEY = ?',
            params=('NASA_API_KEY',),
            fetch_one=True
        )

        if result and result['CONFIG_VALUE']:
            self.nasa_api_key = result['CONFIG_VALUE'] 
        else:
           raise Exception('Failed to fetch nasa api key from config')  

        for cog in get_cog_modules():
            self.load_extension(cog)
            print(f'Successfully loaded cog: {cog}')

    async def close(self):
        if self.config_db:
            close_config_db_connection(self.config_db)
            print('Closed config database connection')
        await super().close()

    async def on_ready(self):
        print(f'{self.user} logged into the mainframe')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name="the sea dogs arena"))


if __name__ == '__main__':
    async def main():
        bot = MonkaMind()

        try:
            await bot.setup_hook()
            await bot.start(bot.token)
        except KeyboardInterrupt:
            print('Stopping monkamind')
        finally:
            await bot.close()

    asyncio.run(main())