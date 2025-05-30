import discord
import asyncio
from discord.ext import commands
from discord.commands import Option

from resources.helper_funcs import *
from monkamind import MonkaMind


USER_SELECTED_IMAGES = {}

class Images(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # MESSAGE COMMAND: select image
    @commands.message_command(
        name="Select Image",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install
        }
    )
    async def select_image(self, ctx: discord.ApplicationContext, message: discord.Message) -> None:
        """
        Allows the user to right click, long press on mobile, on a message with an image to extract and select the image. If an image is found, 
        the function adds the user ID of the user who created the action and the image link to the dictionary: USER_SELECTED_IMAGES. This allows the user to then
        process the image with other commands in the application. This avoids needing full message reading permissions for things like user apps. The selected image lasts in 
        the dictionary for 120 seconds.

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): Context in which the command was invoked
            message (discord.Message): The message being interacted with
        """
        if message.attachments:
            USER_SELECTED_IMAGES[ctx.user.id] = message.attachments[0].url
            await ctx.respond("Image selected", ephemeral=True)
            await self.start_expiry_timer(ctx.user.id)
        else:
            await ctx.respond("No image found in this message", ephemeral=True)

    async def start_expiry_timer(self, user_id: int):
        """
        Hold the user ID and the selected image inside the USER_SELECTED_IMAGES dictionary for 2 minutes before deleting

        Parameters:
            self (commands.Bot): The bot user
            user_id (int): The ID of the user who invoked the select_image command
        """
        await asyncio.sleep(120)
        if user_id in USER_SELECTED_IMAGES:
            del USER_SELECTED_IMAGES[user_id]


    # SLASH COMMAND: magik
    @commands.slash_command(
        description="magik an image",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        }
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def magik(self, ctx: discord.ApplicationContext, message: str = Option(str, "Enter a URL", required=False, default='')) -> None:
        """
        Use the ImageMagik library to distort selected images

        Parameters:
            self (commands.Bot): The bot user
            ctx: (discord.ApplicationContext): Context in which the command was invoked
            message: (discord.commands.Option): Optional parameter for the command to allow the user to provide a direct image link so images outside of discord can be processed
        """
        await ctx.defer()
        try:
            if ctx.user.id in USER_SELECTED_IMAGES:
                url = USER_SELECTED_IMAGES.pop(ctx.user.id)
            else:
                url = message or await find_recent_image_url(ctx)

            if not url:
                await ctx.respond("No recent image found in the last 25 messages.", ephemeral=True)
                return

            buffer = edit_image(url, magik)
            await ctx.respond(file=discord.File(fp=buffer, filename="magik.jpg"))

        except BaseExceptionGroup:
            try:
                url = USER_SELECTED_IMAGES.pop(ctx.user.id)
                buffer = edit_image(url, magik)
            except Exception as ex:
                await ctx.respond(f"Error processing image: {ex}", ephemeral=True)


def setup(bot: MonkaMind):
    bot.add_cog(Images(bot))