from dataclasses import dataclass
import sqlite3
import discord
import asyncio
from discord.ext import commands
import aiohttp
from typing import Any
from datetime import datetime, timezone

from resources.helper_funcs import *
from monkamind import MonkaMind

@dataclass
class Member:
    id: int
    name: str
    created_at: str
    updated_at: str
    avatar: str
    color_main: str
    color_sub: str
    graduated: int

@dataclass
class Channel:
    id: int
    channel: str
    platform_id: int
    member_id: int
    editor_id: int | None
    created_at: str
    updated_at: str


class HoloLiveHelper:
    async def fetch_json(session: aiohttp.ClientSession, endpoint: str, base_url: str) -> dict[str, Any]:
        """
        Fetch a JSON object from the HOLO.DEV API using the specified endpoint

        Parameters:
            session (aiohttp.ClientSession): Active Http session for the HOLO.DEV API
            base_url (str): The base url for the HOLO.DEV API

        Returns:
            dict[str, Any]: A dictionary with the results of the API call to the 
            specified endpoint of the name of each object along with the object
        """
        url = f'{base_url}/{endpoint}'
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def fetch_channel(session: aiohttp.ClientSession, channel_id: int, base_url: str) -> dict[str, Any] | None:
        """
        Fetch a specific channel based on the ID using the /channels endpoint of the HOLO.DEV API

        Parameters:
            session (aiohttp.ClientSession): Active Http session for the HOLO.DEV API
            channel_id (int): The ID that is used as a foriegn key on the /channels endpoint of the HOLO.DEV API
            base_url (str): The base url for the HOLO.DEV API

        Returns:
            dict[str, Any] | None: A dictionary of the channel name and information regarding the channel. None is returned if there is no channel
            that could be found based on the provided channel ID
        """
        url = f'{base_url}/channels/{channel_id}'
        async with session.get(url) as resp:
            if resp.status == 404:
                return None
            resp.raise_for_status()
            return await resp.json()

    async def fetch_all_channels(session: aiohttp.ClientSession, base_url: str) -> list[dict[str, Any]]:
        """
        Fetch all the channels for all hololive members from the HOLO.DEV /channels API endpoint

        Parameters:
            session (aiohttp.ClientSession): Active Http session for the HOLO.DEV API
            base_url (str): The base url for the HOLO.DEV API

        Returns:
            list[dict[str, Any]]: A list of dictioaries where each dictionary represents a channel with a key of the channel name and a value of an object containing 
            information about the channel
        """
        sem = asyncio.Semaphore(10)
        results: list[dict[str, Any]] = []

        async def fetch_with_sem(channel_id: int):
            """
            Fetch each channel indvidually using semaphores

            Parameters:
                channel_id (int): ID used as the primary key to denote a channel in the /channels endpoint of the HOLO.DEV API
            """
            async with sem:
                return await HoloLiveHelper.fetch_channel(session, channel_id, base_url)

        tasks = [fetch_with_sem(i) for i in range(1, 356)]
        channels = await asyncio.gather(*tasks)
        for c in channels:
            if c:
                results.append(c)
        return results

    async def fetch_all_members(session: aiohttp.ClientSession, base_url: str) -> list[dict[str, Any]]:
        """
        Call the /members endpoint of the HOLO.DEV API to get a list of all hololive members (previous and current)

        Parameters:
            session (aiohttp.ClientSession): Active Http session for the HOLO.DEV API
            base_url (str): The base url for the HOLO.DEV API

        Returns:
            list[dict[str, Any]]: A list of a dictionary containing the { "NameOfMember": Member object }
        """
        data = await HoloLiveHelper.fetch_json(session, 'members', base_url)
        return data

    def save_to_sqlite(members: list[dict[str, Any]], channels: list[dict[str, Any]], config_connection: sqlite3.Connection) -> tuple[int, int]:
        cursor = config_connection.cursor()

        cursor.execute('DELETE FROM HOLOLIVE_MEMBERS;')
        cursor.execute('DELETE FROM HOLOLIVE_CHANNELS;')

        member_rows = [
            (
                m['id'],
                m['name'],
                m.get('avatar'),
                m.get('color_main'),
                m.get('color_sub'),
                int(m.get('graduated', False)),
                m.get('created_at'),
                m.get('updated_at')
            )
            for m in members
        ]
        num_member_rows = cursor.executemany("""
            INSERT INTO HOLOLIVE_MEMBERS
            (id, name, avatar, color_main, color_sub, graduated, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, member_rows)

        channel_rows = [
            (
                c["id"],
                c["channel"],
                c.get("platform_id"),
                c.get("member_id"),
                c.get("editor_id"),
                c.get("created_at"),
                c.get("updated_at")
            )
            for c in channels
        ]
        num_channel_rows = cursor.executemany("""
            INSERT INTO HOLOLIVE_CHANNELS
            (id, channel, platform_id, member_id, editor_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, channel_rows)

        return (num_member_rows, num_channel_rows)

class HoloLive(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: MonkaMind = bot
        self.base_api_url: str = 'https://holo.dev/api/v1'

    async def fetch_data(self, endpoint: str) -> dict[str, Any] | None:
        """
        Fetch data for hololive channels using the provided hololive API stored in the config database

        Parameters:
            self (commands.Bot): The bot user
            endpoint (str): The API endpoint being queried

        Returns:
            Dict[str, Any] | None: An optional dictionary containing the JSON data fetched from the API call. If the API call failed or nothing
            was returned, the function will return None
        """
        url = f'{self.base_api_url}/{endpoint}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
            
    def fetch_members(self) -> list[Member]:
        """
        Fetch a list of all the hololive members from the config database. These are stored locally to avoid spamming API endpoints.

        Parameters:
            self (commands.Bot): The bot user

        Returns:
            list[Member]: A list of Member objects that store all the attributes of each channel
        """
        cursor = self.bot.config_db.cursor()
        cursor.execute('SELECT ID, NAME, CREATED_AT, UPDATED_AT, AVATAR, COLOR_MAIN, COLOR_SUB, GRADUATED FROM HOLOLIVE_MEMBERS')
        rows = cursor.fetchall()
        cursor.close()
        return [
            Member(
                id=row[0],
                name=row[1], 
                created_at=row[2],
                updated_at=row[3],
                avatar=row[4],
                color_main=row[5],
                color_sub=row[6],
                graduated=row[7]
            )
            for row in rows
        ]

    def fetch_channels(self) -> list[Channel]:
        """
        Fetch a list of all the hololive channels from the config database. These are stored locally to avoid spamming API endpoints.

        Parameters:
            self (commands.Bot): The bot user

        Returns:
            list[Channel]: A list of Channel objects that store all the attributes of each channel
        """
        cursor = self.bot.config_db.cursor()
        cursor.execute('SELECT ID, CHANNEL, PLATFORM_ID, MEMBER_ID, EDITOR_ID, CREATED_AT, UPDATED_AT FROM HOLOLIVE_CHANNELS')
        rows = cursor.fetchall()
        cursor.close()
        return [
            Channel(
                id=row[0],
                channel=row[1], 
                platform_id=row[2],
                member_id=row[3],
                editor_id=row[4],
                created_at=row[5],
                updated_at=row[6]
            )
            for row in rows
        ]


    def build_embed(
        self,
        title: str, 
        color: discord.Color, 
        streams: list[dict[str, Any]], 
        channel_map: dict[str, dict[str, Any]], 
        member_map: dict[str, dict[str, Any]]
    ) -> discord.Embed:
        """
        Create an embed to display a provided list of channels. This function will map the data returned from the current or scheduled API endpoint
        and use the channels and members endpoints to cross reference information about the channel that is live. Embeds are created using fields with 
        a maximum of 10 channels showing in the returned embed

        Parameters:
            self (commands.Bot): The bot user
            title (str): The title that will display on the embed
            color (discord.Color): The color the embed will display
            streams (list[dict[str, Any]]): A list of dictionaries that stores the response data from the API call to fetch either the currently live or scheduled streams
            channel_map (dict[str, dict[str, Any]]): Used to map a specific channel id to a member id for lookup purposes
            member_map (dict[str, dict[str, Any]]): Used to map a specific member id to a member to get general information about the member such as name and id

        Returns:
            discord.Embed: A completed discord embed object that displays a list of no more than 10 streams based off a provided list of streams
        """
        embed = discord.Embed(title=title, color=color)
        if not streams:
            embed.description = 'No streams found'
            return embed

        for stream in streams[:10]:
            channel_id = stream['channel']
            channel: Channel = channel_map.get(channel_id)
            member: Member = (member_map.get(channel.member_id) if channel else None)

            name = member.name if member else 'Unknown Member'
            stream_title = stream.get('title', 'Utitled Stream')
            stream_url = f'https://www.youtube.com/watch?v={stream['room']}'
            start_time: str = stream.get('start_at', 'TBA')

            try:
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                start_timestamp = int(start_datetime.timestamp())
                now = datetime.now(timezone.utc)
                delta = now - start_datetime

                if delta.total_seconds() >= 0:
                    hours, remainder = divmod(int(delta.total_seconds()), 3600)
                    minutes = remainder // 60
                    live_for = f'{hours} Hours and {minutes} Minutes'
                    time_info = f'⌛ Started: <t:{start_timestamp}:f>\nLive for: **{live_for}**'
                else:
                    time_info = f'⌛ Scheduled: <t:{start_timestamp}:f>'
            except:
                time_info = f'⌛ Scheduled: <t:{start_timestamp}:f>'

            embed.add_field(
                name=f'{name}',
                value=f'[{stream_title}]({stream_url})\n{time_info}',
                inline=False
            )
        return embed
    
    @commands.slash_command(
        name='hololive_schedules', description='Show live and scheduled lives for hololive members',
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        }
    )
    @commands.cooldown(rate=1, per=60.0, type=commands.BucketType.user)
    async def hololive_schedules(self, ctx: discord.ApplicationContext) -> None:
        """
        Slash command to allow a user to display currently live and currently scheduled to be live channels of hololive members. This command exclusively displays 
        information regarding youtube channels for members. This command will display the first 10 members that are currently live fetched from the HOLO.DEV API and 
        display the first 10 members fetched from the API that are are scheudled to be live. This command generates two embeds: one for live channels and the other for 
        scheduled to be live channels.

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
        """
        await ctx.defer()

        current_lives = await self.fetch_data('lives/current')
        scheduled = await self.fetch_data('lives/scheduled')
        members = self.fetch_members()
        channels = self.fetch_channels()

        if not current_lives or not scheduled or not channels or not members:
            await ctx.followup.send('Failed to fetch live stream data')
            return

        channel_map = {channel.channel: channel for channel in channels if channel.platform_id == 1}
        member_map = {member.id: member for member in members}

        live_embed = self.build_embed(
            '🔴 Currently Live',
            discord.Color.red(),
            current_lives.get('lives', []),
            channel_map,
            member_map
        )

        scheduled_embed = self.build_embed(
            '⏳ Scheduled Live Streams',
            discord.Color.blue(),
            scheduled.get('lives', []),
            channel_map,
            member_map
        )

        await ctx.followup.send(embeds=[live_embed, scheduled_embed])


    @commands.slash_command(
        name='update_hololive_database', description='Update the hololive members and channels tables in the config database'
    )
    @commands.cooldown(rate=1, per=60.0, type=commands.BucketType.user)
    @is_admin()
    async def update_hololive_database(self, ctx: discord.ApplicationContext) -> None:
        """
        Command to let a bot administrator refresh the config database with updated channels and members fetched from the HOLO.DEV API. This command will delete everything in the 
        HOLOLIVE_MEMBERS and HOLOLIVE_CHANNELS tables in the config database.

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
        """
        await ctx.defer()

        response_messsage = await ctx.respond('Updating hololive members and channels tables')
        async with aiohttp.ClientSession() as session:
            response_messsage.edit_original_message('Fetching Hololive data from HOLO.DEV...')

            members = await HoloLiveHelper.fetch_all_members(session, self.base_api_url)
            response_messsage.edit_original_message(f'Fetched {len(members)} members')

            channels = await HoloLiveHelper.fetch_all_channels(session, self.base_api_url)
            response_messsage.edit_original_message(f'Fetched {len(channels)} channels')

            data_insert_count = HoloLiveHelper.save_to_sqlite(members, channels, self.bot.config_db)
            response_body = f"""
                ```\n
                Number of rows inserted into the members table: {data_insert_count[0]}\n
                Number of rows inserted into the channels table: {data_insert_count[1]}\n
                ```
            """
            response_messsage.edit_original_message(response_body)



def setup(bot: MonkaMind):
    bot.add_cog(HoloLive(bot))