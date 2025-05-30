import discord
import requests
from discord.ext import commands
from discord.commands import Option
from discord.ext.pages import Paginator, Page

from monkamind import MonkaMind

class RocketLaunches(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: MonkaMind = bot

    @commands.slash_command(description="Displays upcoming rocket launches")
    async def rocketlaunches(self, ctx: discord.ApplicationContext):
        """
        Create a Paginator object that displays the next 10 upcoming rocket launches with each launch being assigned a page that has an embed detailing about the launch

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
        """
        await ctx.defer()
        request = requests.get("https://ll.thespacedevs.com/2.2.0/launch/upcoming")
        result_data = request.json()

        launchesList = []

        for data in result_data["results"]:
            launchInfo = []

            if data['name']:
                name = data['name']
            else:
                name = "N/A"
            if data['window_start'] and data['window_end']:
                window_start = data['window_start']
                window_end = data['window_end']
            else:
                window_start = "N/A"
                window_end = "N/A"
            if data['probability'] and data['probability'] != -1:
                probability = str(data['probability']) + "%"
            elif data['probability'] and data['probability'] == -1:
                probability = "TBD"
            else:
                probability = "N/A"
            if data['launch_service_provider']['name']:
                provider = data['launch_service_provider']['name']
            else:
                provider = "N/A"
            if data['rocket']['configuration']['full_name']:
                full_name = data['rocket']['configuration']['full_name']
            else:
                full_name = "N/A"
            if data['mission']:
                mission_desc = data['mission']['description']
            else:
                mission_desc = "N/A"
            if data['pad']['name'] and data['pad']['location']['name']:
                pad_name = data['pad']['name']
                pad_loc = data['pad']['location']['name']
            else:
                pad_name = "N/A"
                pad_loc = "N/A"
            map_image = data['pad']['map_image']
            small_image = data['image']

            launchInfo.append(name)
            launchInfo.append(provider)
            launchInfo.append(full_name)
            launchInfo.append(probability)
            launchInfo.append((window_start,window_end))
            launchInfo.append((pad_name, pad_loc))
            launchInfo.append(mission_desc)
            launchInfo.append(map_image)
            launchInfo.append(small_image)

            launchesList.append(launchInfo)
            
        pages = []
        for launch in launchesList:
            embed = discord.Embed(
                title = launch[0],
                description = f"""Provider: {launch[1]}
                Rocket: {launch[2]}
                Weather Conditions: {launch[3]}
                Launch Window: {launch[4][0]} - {launch[4][1]}

                Mission: {launch[6]}  
                """,
                color = discord.Color.red()
            )
            embed.add_field(name=f"Pad: {launch[5][0]} | {launch[5][1]}", value="\u200B")
            embed.set_image(url=launch[7])
            embed.set_thumbnail(url=launch[8])
            pages.append(Page(embeds=[embed]))
        paginator = Paginator(pages=pages, loop_pages=True, use_default_buttons=True, disable_on_timeout=True)
        await paginator.respond(ctx.interaction, ephemeral=False)


def setup(bot: MonkaMind):
    bot.add_cog(RocketLaunches(bot))