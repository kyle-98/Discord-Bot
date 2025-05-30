import discord
from discord.ext import commands
from datetime import datetime

from monkamind import MonkaMind
from bot_config.config import execute_query
from resources.helper_funcs import is_admin

class ClockIn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: MonkaMind = bot

    @commands.slash_command(
        name="clockin",
        description="Is it clock in time?",
        integration_types={discord.IntegrationType.guild_install}
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clockin(self, ctx: discord.ApplicationContext) -> None:
        """
        Let the user clock in to work to start a day of slaving away deep in the heart of corporate america

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): Context in which the command was invoked
        """
        await ctx.defer()

        TODAYS_DATE = str(datetime.today())[0:10]
        user_id = ctx.author.id
        # Check if the user has clocked in today
        query = 'SELECT TIMES_CLOCKED_IN, LAST_TIME FROM CLOCKIN WHERE USER_ID = ?'
        params = (str(user_id),)
        result = execute_query(
            config_connection=self.bot.config_db, 
            query=query,
            params=params,
            fetch_one=True
        )
        if result == None:
            await ctx.respond(f'Failed to fetch clock in data', ephemeral=True)
        elif len(result) == 0:
            # add user to table for first time clock in
            query = 'INSERT INTO CLOCKIN VALUES (?, ?, ?)'
            params=(user_id, '1', TODAYS_DATE)
            execute_query(
                config_connection=self.bot.config_db,
                query=query,
                params=params,
                fetch_all=False
            )
            await ctx.respond('You have been clocked in')
        else:
            times_clocked_in = int(result['TIMES_CLOCKED_IN'])
            last_time = result['LAST_TIME']
            last_date = datetime.strptime(last_time, '%Y-%m-%d')
            today_date = datetime.strptime(TODAYS_DATE, '%Y-%m-%d')
            if today_date == last_date:
                await ctx.respond(f'You have already clocked in for today', ephemeral=True)
            elif today_date > last_date:
                query = 'UPDATE CLOCKIN SET TIMES_CLOCKED_IN = ?, LAST_TIME = ? WHERE USER_ID = ?'
                params = (times_clocked_in + 1, TODAYS_DATE, user_id)
                execute_query(
                    config_connection=self.bot.config_db,
                    query=query, 
                    params=params,
                    fetch_all=False
                )
                await ctx.respond('You have been clocked in')

    @commands.slash_command(
        description="Display the clock in leaderboard",
        integration_types={discord.IntegrationType.guild_install}
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clockinleaderboard(self, ctx: discord.ApplicationContext) -> None:
        """
        Display a list of all users who have ever clocked in

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): Context in which the command was invoked
        """
        await ctx.defer()

        query = 'SELECT USER_ID, TIMES_CLOCKED_IN FROM CLOCKIN ORDER BY TIMES_CLOCKED_IN DESC'
        result = execute_query(
            config_connection=self.bot.config_db,
            query=query
        )
        if result == None:
            await ctx.respond('Failed to fetch clockin leaderboard', ephemeral=True)

        elif len(result) == 0:
            await ctx.respond('No users to display on the clockin leaderboard', ephemeral=True)
            return
        
        # Build a code block to display the text somewhat formatted
        text_list = ['```', f"{'#':<5}{'User':<20}{'Clock-Ins'}", '-' * 35]
        for index, info in enumerate(result):
            user = await self.bot.fetch_user(info['USER_ID'])
            username = user.name 
            text_list.append(f"{index + 1:<5}{username:<20}{info['TIMES_CLOCKED_IN']} clock-ins")
        text_list.append('```')
        embed_body = '\n'.join(text_list)

        embed = discord.Embed(
            title="Top Clock-In Workers 📈",
            description=embed_body,
            timestamp=datetime.now(),
            color=discord.Color.gold()
        )

        await ctx.respond(embed=embed)

    
    @commands.slash_command(description='Set a users times clocked in')
    @is_admin()
    async def setclockin(self, ctx: discord.ApplicationContext, user_id: str, times: int) -> None:
        await ctx.defer()
        execute_query(
            config_connection=self.bot.config_db,
            query='UPDATE CLOCKIN SET TIMES_CLOCKED_IN = ? WHERE USER_ID = ?',
            params=(times, int(user_id)),
            fetch_all=False
        )
        username = await self.bot.fetch_user(user_id)
        await ctx.respond(f"Set {username}'s clock-in times to {times}", ephemeral=True)


def setup(bot: MonkaMind):
    bot.add_cog(ClockIn(bot))