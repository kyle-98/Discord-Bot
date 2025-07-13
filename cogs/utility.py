import sys
import traceback
import discord
from discord.ext import commands
from discord.commands import Option

from resources.exceptions import NotAdmin

from monkamind import MonkaMind
from bot_config.config import execute_query

class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: MonkaMind = bot


    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error) -> None:
        """
        If the bot encounters errors in any command run by the user, this method will trigger globally to catch these errors

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): Context in which the command was invoked
            error (Any): Exception being caught
        """
        if isinstance(error, NotAdmin):
            await ctx.respond('You are not authorized to use this command', ephemeral=True)
        else:
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            print(error)
            await ctx.respond(error, ephemeral=True)
        

    @commands.slash_command(description="Manage bot administrators")
    @commands.is_owner()
    async def manageadmins(self, ctx: discord.ApplicationContext, user_id: str, action = Option(str, choices=['add', 'remove'], required=True)) -> None:
        """
        Bot owner only slash command to allow the owner of the bot to add or remove users based on a provided user ID to the administrators group table in the config database

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): Context in which the command was invoked
            user_id (str): User ID of the user whose group is being modified
            action (discord.Option): A required option to choose either add or remove
        """
        username = await self.bot.fetch_user(user_id)
        if action == 'add':
            execute_query(
                config_connection=self.bot.config_db,
                query='INSERT INTO ADMINS (USER_ID) VALUES (?)',
                params=(user_id,),
                fetch_all=False
            )
            await ctx.respond(f'Successfully added {username} to the administrators group')
        elif action == 'remove':
            execute_query(
                config_connection=self.bot.config_db,
                query='DELETE FROM ADMINS WHERE USER_ID = ?',
                params=(user_id,),
                fetch_all=False
            )
            await ctx.respond(f'Successfully removed {username} to the administrators group', ephemeral=True)

    # Pin selected messaage to pins channel (pins channel is defined in the config.db as CONFIG_KEY = PIN_CHANNEL_ID)
    @commands.message_command(name="Pin Message")
    async def pin_message(self, ctx: discord.ApplicationContext, message: discord.Message) -> None:
        """
        Creates an embed and sends the embed of a selected image into a predefined pins channel. This recreates discord pin functionality except with a predefined channel for output
        and no limit on the number of pins.

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): Context in which the command was invoked
            message (discord.Message): Object which contains the selected discord message
        """

        # Get the content of the message selected and create a template embed that will be used for the pinned message
        msg = await ctx.fetch_message(message.id)
        response_embed = discord.Embed(
            url=msg.jump_url,
            title=f"Message By {str(msg.author)[:-2]}",
            description=(f"{msg.content}"),
            timestamp=msg.created_at  
        )
        # pins channel is defined in the config.db as CONFIG_KEY = PIN_CHANNEL_ID
        pin_channel_id = self.bot.pin_channel_id
        # Fetch the pinned messages channel defined above into memory
        channel = await self.bot.fetch_channel(pin_channel_id)

        # Check for multiple attachments in the message
        if(len(msg.attachments) > 0):
            # If the message selected is a file (e..g. docx, PDF, xlsx)
            if(msg.attachments[0].content_type == None):
                await channel.send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n**File Name: *{msg.attachments[0].url.split('/')[-1]}***\n{msg.attachments[0].url}")
            # If the message selected is an application file (e.g. zip, exe, rar)
            elif(msg.attachments[0].content_type.startswith("application")):
                if(msg.content == ""):
                    embed = discord.Embed(
                        url=msg.jump_url,
                        title=f"Message by: {str(msg.author)[:-2]}",
                        description=f"Filename: {msg.attachments[0].url.split('/')[-1]}\n\n[Download Link]({msg.attachments[0].url})",
                        timestamp=msg.created_at
                    )
                    await channel.send(embed=embed)
                else:
                    embed = discord.Embed(
                        url=msg.jump_url,
                        title=f"Message by: {str(msg.author)[:-2]}",
                        description=f"__Message:__ {msg.content}\n\n__Filename:__ {msg.attachments[0].url.split('/')[-1]}\n\n[Download Link]({msg.attachments[0].url})",
                        timestamp=msg.created_at
                    )
            # If the message selected contains a video, embed the video so it is playable in the pinned message
            elif(msg.attachments[0].content_type.startswith("video")):
                await channel.send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n{msg.attachments[0]}")
            # If the message selected just contains standard picture attachments
            else:
                attach_embeds = []
                res_embed = discord.Embed(
                    url=msg.jump_url,
                    title=f"Message by: {str(msg.author)[:-2]}",
                    description=f"{msg.content}",
                    timestamp=msg.created_at
                )
                attach_embeds.append(res_embed)
                for i in range(0, len(msg.attachments)):
                    res = discord.Embed(
                    url=msg.jump_url
                    )
                    res.set_image(url=msg.attachments[i])
                    attach_embeds.append(res)
                await channel.send(embeds=attach_embeds)
        # If the message selected is just plain text
        else:
            await channel.send(embed=response_embed)
        # Send a link in the channel where the message originates from linking to the newly pinned message in the pinned messages channel
        await ctx.respond(f"Message: [Jump to message]({msg.jump_url})\n**Pinned by {str(ctx.author)[:-2]}**")


def setup(bot: MonkaMind):
    bot.add_cog(Utility(bot))