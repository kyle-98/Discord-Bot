import discord
import requests
from discord.ext import commands
from discord.commands import Option
from geopy.geocoders import Nominatim
from io import BytesIO

from monkamind import MonkaMind
from resources.helper_funcs import get_latlong


def get_nasa_image_url(lat: str, lon: str, api_key: str, dim: int = 0.15):
    url = 'https://api.nasa.gov/planetary/earth/imagery'
    params = {
        'lat': lat,
        'lon': lon,
        'dim': dim,
        'api_key': api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.url
    else:
        print("Error:", response.status_code, response.text)
        return None


class NASA(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: MonkaMind = bot

    @commands.slash_command(name='nsa', 
        description='Look at this dudes house',
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        }
    )
    async def nsa(self, ctx: discord.ApplicationContext, location = discord.Option(str, 'Enter a city or address', required=True)):
        await ctx.defer()
        coords = get_latlong(location, self.bot.geopy_username)
        if not coords:
            await ctx.respond('Could not convert location to coordinates')
            return
        
        lat, lon = coords
        image_url = get_nasa_image_url(lat, lon, self.bot.nasa_api_key)
        if not image_url:
            await ctx.respond('NSA agents could not get satellite imagery of the location')
            return

        embed = discord.Embed(
            title='<:exclaim:1377449136995041422>',
            description=f'Coordinates: `{lat:.4f}, {lon:.4f}`',
            color=discord.Color.blurple()
        )
        embed.set_image(url=image_url)
        
        await ctx.respond(embed=embed)


def setup(bot: MonkaMind):
    bot.add_cog(NASA(bot))