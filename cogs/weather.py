import discord
from discord.ext import commands
import random
from tropycal import utils, realtime, tracks
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from datetime import datetime
import io
from io import BytesIO
import requests
from PIL import Image as im

from monkamind import MonkaMind
from resources.helper_funcs import get_latlong, check_years, check_date


def gen_gif_map(base_url: str, model: str) -> BytesIO | None:
    image_links = []
    gif_frames = []
    
    if len(base_url) == 2:
        if model in ('gdps', 'ecmwf'):
            nums = [f'{i:03d}' for i in range(6, 241, 6)]
        else:
            nums = [f'{i:03d}' for i in range(6, 385, 6)]
        for i in nums:
            image_links.append(f'{base_url[0]}{i}/{base_url[1]}')
    else:
        count = 40 if model == 'gem' else 64
        for i in range(1, count + 1):
            image_links.append(f'{base_url[0]}{i}.png')

    if 'tropicaltidbits' in base_url[0]:
        referer = 'https://www.tropicaltidbits.com/'
    else:
        referer = 'https://www.pivotalweather.com/'

    for index, link in enumerate(image_links):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': referer,
            'Connection': 'keep-alive'
        }
        response = requests.get(link, headers=headers)
        print(f'Found image #: {index}')
        if response.status_code == 404:
            print(f'404 at {link}, canceling.')
            return None
        try:
            image = im.open(BytesIO(response.content)).convert("RGB")
            gif_frames.append(image)
        except Exception as e:
            print(f"Error loading image ({link}): {e}")
            return None
    if not gif_frames:
        return None

    # Save to memory instead of disk
    gif_buffer = BytesIO()
    gif_frames[0].save(
        gif_buffer,
        format='GIF',
        append_images=gif_frames[1:],
        save_all=True,
        loop=0
    )
    gif_buffer.seek(0)
    print('Done generating gif in memory')
    return gif_buffer

#Autocomplete autofill options for precip type based on the model choice
def get_precip_types(ctx: discord.AutocompleteContext) -> list[str]:
    """
    Generate a list of options based on user selection of a weather model. These options list the type of precip that can
    be depicted on a model map based on the model chosen by the user

    Parameters:
        ctx (discord.AutocompleteContext): The choice the user provided when executing the slash command

    Returns:
        list[str]: A list of the supported precip types by the model chosen from the user
    """
    model_type = ctx.options['model']
    if model_type == 'ecmwf':
        return ['mslp']
    else:
        return ['mslp', 'snow']

#Autocomplete autofill options for region based on the website choice
def get_regions(ctx: discord.AutocompleteContext) -> list[str]:
    """
    Get a list of supported regions based on the source site the user chose when executing the slash command

    Parameters:
        ctx (discord.AutocompleteContext): The choice the user provided when executing the slash command

    Returns:
        list[str]: A list of strings that details all the available regions of the US that are supported by the user's source site choice
    """
    site = ctx.options['site']
    if site == 'tropicaltidbits':
        return ['CONUS', 'North-West', 'North-Central', 'North-East', 'Eastern', 'South-West', 'South-Central', 'South-East', 'Western']
    else:
        return ['CONUS', 'North-West', 'North-Central', 'North-East', 'Mid-Atlantic','Sout-West', 'South-Central', 'South-East', 'Mid-West',]

def gen_base_url(site: str, model: str, type: str, time: str, region: str, date: str) -> BytesIO | None:
    """
    Generate a list of all the images fetched from a source site for all the frames of the model run chosen by the user. This function fetches all the images into a list and stitches them together using 
    the gen_gif_map function.

    Parameters:
        site (str): The source site the function will fetch the gif frames from
        model (str): The source model the function will fetch the gif frames from
        type (str): The type of precip that will be depicted in the frames
        time (str): The Z time in which the model run that is getting fetched was run
        region (str): The region of the US that the model will be depicting
        date (str): The date of the day the model run pertains to

    Returns:
        BytesIO: A completed gif of all the frames of the specified model run
    """
    tt_dict = {
        'CONUS': 'us',
        'North-West': 'nwus',
        'North-Central': 'ncus',
        'North-East': 'neus',
        'Eastern': 'eus',
        'South-West': 'swus',
        'South-Central': 'scus',
        'South-East': 'seus',
        'Western': 'wus'
    }
    pw_dict = {
        'CONUS': 'conus',
        'North-West': 'us_nw',
        'North-Central': 'us_nc',
        'North-East': 'us_ne',
        'Mid-Atlantic': 'us_ma',
        'South-West': 'us_sw',
        'South-Central': 'us_sc',
        'South-East': 'us_se',
        'Mid-West': 'us_mw'
    }
    if site == 'tropicaltidbits':
        if model == 'cmc':
            model = 'gem'
        base_url = [f'https://www.tropicaltidbits.com/analysis/models/{model}/{date[0]}{date[1]}{date[2]}{time}/{model}_']
        if type == 'mslp':
            if model == 'ecmwf':
                base_url[0] += f'mslp_pcpn_{tt_dict[region]}_'
            else:
                base_url[0] += f'mslp_pcpn_frzn_{tt_dict[region]}_'
        else:
            base_url[0] += f'asnow_{tt_dict[region]}_'
    else:
        if model == 'cmc':
            model = 'gdps'
        if model == 'ecmwf':
            model = 'ecmwf_full'
        base_url = [f'https://m1o.pivotalweather.com/maps/models/{model}/{date[0]}{date[1]}{date[2]}{time}/']
        if type == 'mslp':
            if 'ecmwf' in model:
                base_url.append(f'prateptype_cat_ecmwf-imp.{pw_dict[region]}.png')
            else:
                base_url.append(f'prateptype_cat-imp.{pw_dict[region]}.png')
        else:
            base_url.append(f'sn10_acc-imp.{pw_dict[region]}.png')
    map_buffer = gen_gif_map(base_url, model)
    return map_buffer



class CPCOutlookView(discord.ui.View):
    def __init__(self, *items, timeout = 180, disable_on_timeout = True):
        super().__init__(*items, timeout=timeout, disable_on_timeout=disable_on_timeout)

    @discord.ui.select(
        placeholder = 'Choose an option',
        min_values = 1,
        max_values = 1,
        options = [
            discord.SelectOption(
                label="6 to 10 Day Outlook",
                description="Get CPC 6-10 Day Outlook Maps"
            ),
            discord.SelectOption(
                label="8 to 14 Day Outlook",
                description="Get CPC 8-14 Day Outlook Maps"
            )
        ]
    )
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction) -> None:
        """
        Callback to handle the user selection of the discord.ui.select element

        Parameters:
            self (commands.Bot): The bot user
            select (discord.ui.Select): The select view which contains the selected values from the user's interaction
            interaction (discord.Interaction): The interaction the user made with the select view element. Allows the bot to respond to the interaction of selecting an item from the select view
        """
        await interaction.response.defer()

        if select.values[0] == "6 to 10 Day Outlook":
            temp_outlook_embed = discord.Embed(
                url="https://www.cpc.ncep.noaa.gov/products/predictions/610day/",
                title=f"6 to 10 Day Outlook",
                description="6 to 10 Day Outlook from the Climate Prediction Center",
                color=discord.Color.blue()
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            temp_outlook_embed.set_image(url=f"https://www.cpc.ncep.noaa.gov/products/predictions/610day/610temp.new.gif{unique_query_param}")

            precip_outlook_embed = discord.Embed(
                url="https://www.cpc.ncep.noaa.gov/products/predictions/610day/"
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            precip_outlook_embed.set_image(url=f"https://www.cpc.ncep.noaa.gov/products/predictions/610day/610prcp.new.gif{unique_query_param}")
            await interaction.followup.send(embeds=[temp_outlook_embed, precip_outlook_embed])

        elif select.values[0] == "8 to 14 Day Outlook":
            temp_outlook_embed = discord.Embed(
                url="https://www.cpc.ncep.noaa.gov/products/predictions/814day/",
                title=f"8 to 14 Day Outlook",
                description="8 to 14 Day Outlook from the Climate Prediction Center",
                color=discord.Color.blue()
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            temp_outlook_embed.set_image(url=f"https://www.cpc.ncep.noaa.gov/products/predictions/814day/814temp.new.gif{unique_query_param}")

            precip_outlook_embed = discord.Embed(
                url="https://www.cpc.ncep.noaa.gov/products/predictions/814day/"
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            precip_outlook_embed.set_image(url=f"https://www.cpc.ncep.noaa.gov/products/predictions/814day/814prcp.new.gif{unique_query_param}")
            await interaction.followup.send(embeds=[temp_outlook_embed, precip_outlook_embed])

class TropicalView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180, disable_on_timeout=True)

    @discord.ui.select(
        placeholder='Choose an option',
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="2-Day Graphical Outlook", description="Two-day outlook for tropical weather (AL)"),
            discord.SelectOption(label="7-Day Graphical Outlook", description="Seven-day outlook for tropical weather (AL)")
        ]
    )
    async def select_callback(self, select: discord.SelectOption, interaction: discord.Interaction) -> None:
        """
        The callback function that is triggered when the user interacts with the TropicalView select dropdown options. This will fetch the image that shows the tropical outlook 
        based on the period the user selected in the interaction.

        Parameters:
            self (commands.Bot): The bot user
            select (discord.SelectMenu): The selection option chosen by the user
            interaction (discord.Interaction): The interaction the user had with the select menu
        """
        await interaction.response.defer()
        days = "2" if "2-Day" in select.values[0] else "7"
        embed = discord.Embed(
            url=f"https://www.nhc.noaa.gov/gtwo.php?basin=atlc&fdays={days}",
            title=f"Atlantic {days}-Day Graphical Tropical Weather Outlook"
        )
        embed.set_image(url=f"https://www.nhc.noaa.gov/xgtwo/two_atl_{days}d0.png?random={random.randint(1, 1000)}")
        await interaction.followup.send(embed=embed)


class TropicalStormDropDown(discord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Choose a storm",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        """
        Callback function used to handle the user interaction with the select dropdown. When the user picks an option from the dropdown this function
        will be run to generate the plot for the selected tropical storm.

        Parameters:
            self (commands.Bot): The bot user
            interaction (discord.Interaction): The interaction event the user triggered
        """
        await interaction.response.defer()
        status_msg = await interaction.followup.send("Generating... <a:spin:1149889506628096161>")

        name, storm_id = self.values[0].split(' | ')
        storm = realtime.Realtime().get_storm(storm_id)
        fig = plt.figure(figsize=(11, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        self.plot_boundaries(ax)
        ax = utils.add_tropycal(ax)
        storm.plot_forecast_realtime(ax=ax)
        lat = storm.get_forecast_realtime()['lat'][0]
        lon = storm.get_forecast_realtime()['lon'][0]
        ax.set_extent([lon - 40, lon + 15, lat + 20, lat - 15])
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        buffer.seek(0)

        storm_type = storm.get_forecast_realtime()['type'][0]
        storm_type = 'Tropical Storm' if storm_type == 'TS' else 'Hurricane' if storm_type == 'HU' else storm_type
        embed = discord.Embed(title=f"NHC Track for {storm_type} {storm.name}")
        file = discord.File(fp=buffer, filename='track.png')
        embed.set_image(url='attachment://track.png')
        await status_msg.edit(content="", file=file, embed=embed)

    def plot_boundaries(self, ax: plt.axes) -> None:
        """
        Add features to the plot. This includes: states, borders, coastlines, and land features

        Parameters:
            self (commands.Bot): The bot user
            ax (plt.axes): The axes in which the features will be added to
        """
        ax.add_feature(cfeature.STATES.with_scale('50m'), linewidths=0.5, edgecolor='k')
        ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidths=1.0, edgecolor='k')
        ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=1.0, edgecolor='k')
        ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#EEEEEE')


class TropicalStormsView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=180, disable_on_timeout=True)
        self.add_item(TropicalStormDropDown(options))


def plot_boundaries(ax: plt.axes) -> plt.axes:
    """
    Add features to the plot axes such as states, borders, coastline, and land.

    Parameters:
        ax (plt.axes): The plot axes where the features are going to be added to

    Returns:
        plt.axes: The plot axes that has been updated with the features
    """
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidths=0.5, linestyle='solid', edgecolor='k')
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidths=1.0, linestyle='solid', edgecolor='k')
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=1.0, linestyle='solid', edgecolor='k')
    ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#EEEEEE', edgecolor='face')
    return ax




class Weather(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: MonkaMind = bot
        self.storms = []
        self.storm_data_datetime = datetime.min
        self.update_storm_data()

    def update_storm_data(self):
        """
        Used for refreshing the storm data. Once the bot is initialized, this function will be called by the updatetropicalstorms command to refresh the data with current tropical 
        storms data

        Parameters:
            self (commands.Bot): The bot user
        """
        self.storms = realtime.Realtime().list_active_storms(basin='all')
        self.storm_data_datetime = datetime.now()

    def generate_options(self):
        """
        Used for generating the options for the tropicalstorms command. This will get a list of all the current storms

        Parameters:
            self (commands.Bot): The bot user
        """
        selection_options = []
        for s in self.storms:
            storm = realtime.Realtime().get_storm(s)
            if not storm.invest:
                selection_options.append(discord.SelectOption(
                    label=f"{storm.name} | {storm.id}",
                    description=f"This storm is located in the {storm.basin}"
                ))
        return selection_options

    @commands.slash_command(
        description="Get CPC Outlook Maps",
        integration_types={
            discord.IntegrationType.guild_install,
            discord.IntegrationType.user_install,
        }
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cpcoutlook(self, ctx: discord.ApplicationContext) -> None:
        """
        Command to allow the user to show a select view so they can pick from either the 6-10 or the 8-14 day outlooks from the CPC

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
        """
        await ctx.respond("Choose an outlook", view=CPCOutlookView())

    @commands.slash_command(description="Get NHC Tropical Outlook Maps")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def tropicaloutlook(self, ctx: discord.ApplicationContext):
        """
        Command to generate the TropicalView() select options to the user. This will allow the user to select one of the available options for a tropial outlook

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
        """
        await ctx.respond("Choose an option", view=TropicalView())

    @commands.slash_command(description="Get NHC Prediction Plots")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def tropicalstorms(self, ctx: discord.ApplicationContext):
        """
        Command to generate and display the TropicalStormsView() select options to the user. This command will fetch all the active storms and allow the user to pick from one to
        start the process of plotting it on a map

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
        """
        await ctx.defer()
        options = self.generate_options()

        if not options:
            await ctx.respond('There are no active tropical systems')
            return

        await ctx.respond(
            f"This data is {round((datetime.now() - self.storm_data_datetime).total_seconds() / 60, 2)} minute(s) old. Use /updatetropicalstorms to refresh it",
            view=TropicalStormsView(options)
        )

    @commands.slash_command(description="Update the tropical storm data with most recent data")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def updatetropicalstorms(self, ctx: discord.ApplicationContext) -> None:
        """
        Command to update the tropical storm data. This repopulates the select option the user is shown when running the tropicalstorms command.

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
        """
        await ctx.respond("Updating... <a:spin:1149889506628096161>")
        self.update_storm_data()
        await ctx.send("All Storm Data is now updated.")


    @commands.slash_command(description='Generate map of all tropical cyclones from a given location')
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def cyclonehistory(
        self,
        ctx: discord.ApplicationContext, 
        location = discord.Option(str, 'Provide: City, State or: City, Country', required=True),
        radius = discord.Option(int, 'Radius, in km, around point to draw storm tracks', choices=[50, 100, 150], required=True),
        dots_or_lines = discord.Option(str, 'Map will have dots or lines for tracks', choices=['dots', 'lines'], required=True),
        year_range = discord.Option(str, 'Year range, must be YYYY-YYYY: 1851-PRESENT, oldest year has to be >= 1851', default=None)
    ) -> None:
        """
        Command to let the user generate a plot of all the cyclone tracks over a given area and year timeframe. 

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
            location (discord.Option): Required option of the provided City, State or City, Country
            radius (discord.Option): Required option of the radius in kilometers of where to draw storm tracks intersecting. Choices = 50, 100, 150
            dots_or_lines (discord.Option): Required option to choose if the storm tracks should use solid or dotted lines on the plot
            year_range (discord.Option): Optional parameter to allow the user to choose to only plot storms that occured in a specified time range. The lower end of the boundry must be >= 1851
        """
        await ctx.defer()
        proj = ccrs.PlateCarree()
        fig = plt.figure(figsize=(11,8))
        ax = plt.axes(projection=proj) 
        ax = plot_boundaries(ax)
        ax = utils.add_tropycal(ax)
        basin = tracks.TrackDataset(basin='both', include_btk=True)
        try:
            latlon = get_latlong(loc=location, username=self.bot.geopy_username)
        except:
            await ctx.followup.send('Invalid location string provided.')
        
        try:
            if year_range:
                year_check = check_years(year_range)
                if year_check:
                    yr = year_range.split('-')
                    if dots_or_lines == 'lines':
                        basin.plot_analogs_from_point((latlon[0],latlon[1]),year_range=(int(yr[0]), int(yr[1])),radius=radius,prop={'dots':False,'linecolor':'category'},ax=ax)
                    else:
                        basin.plot_analogs_from_point((latlon[0],latlon[1]),year_range=(int(yr[0]), int(yr[1])),radius=radius,ax=ax) 
                else:
                    await ctx.followup.send('Invalid year range')
            else:
                if dots_or_lines == 'lines':
                    basin.plot_analogs_from_point((latlon[0],latlon[1]),radius=radius,prop={'dots':False,'linecolor':'category'},ax=ax)
                else:
                    basin.plot_analogs_from_point((latlon[0],latlon[1]),radius=radius,ax=ax)

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.show(block=False)
            plt.close()
            buffer.seek(0)
            loc_split = location.split(', ')
            embed = discord.Embed(
                title=f'TC Tracks within a {radius} km range of {loc_split[0]}, {loc_split[1]}'
            )
            file = discord.File(fp=buffer, filename='history.png')
            embed.set_image(url='attachment://history.png')
            await ctx.followup.send(file=file, embed=embed)
        except:
            await ctx.followup.send('An error occured, try again.')


    #Generate gif based on tropical tidbits or pivotal weather GFS/ECWMF/CMC maps
    @commands.slash_command(description='Generate gif based on tropical tidbits or pivotal weather GFS/ECMWF/CMC maps')
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def modelgifs(
        self,
        ctx: discord.ApplicationContext,
        site = discord.Option(str, choices=['tropicaltidbits', 'pivotalweather'], required=True),
        model = discord.Option(str, choices=['gfs', 'ecmwf', 'cmc'], required=True),
        type = discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_precip_types), required=True),
        time = discord.Option(str, choices=['00', '06', '12', '18'], required=True),
        region = discord.Option(str, 'Region of the US', autocomplete=discord.utils.basic_autocomplete(get_regions), required=True),
        date = discord.Option(str, 'Use the format: YYYY-MM-DD', required=True)
    ) -> None:
        """
        Slash command to generate a gif of the max model forecase of a specified weather model. This command lets the user provide a source for the data from either 
        pivotal weather or tropicaltidbits. This function will grab all the frames of the model output run based on the time slot the user specified. 

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
            site (discord.Option): A required option between either tropicaltidbits or pivotalweather. This chooses the source of the gif frames
            model (discord.Option): A required option for the user to choose a weather model (gfs, ecwmf, cmc)
            type (discord.Option): A required option for the user to choose the precip types that will be depicted on the resulting gif. These are generated by the get_precip_types function
            time (discord.Option: A required option for the user to select the Z time from which model run will be depicted
            region (discord.Option): A required option for the region in the US that will be displayed in the resulting gif. These options are generated by the get_regions function
            date (discord.Option): A required option for the date the user is looking for the model run from
        """
        await ctx.defer()
        cd = check_date(date)
        td = date.split('-')
        if not cd:
            await ctx.followup.send('That is not a valid date')
        elif datetime(int(td[0]), int(td[1].lstrip('0')), int(td[2].lstrip('0'))) > datetime.today():
            await ctx.followup.send('You cannot use dates in the future')
        else:
            gif_buffer = gen_base_url(site, model, type, time, region, td)
            if not gif_buffer:
                await ctx.followup.send('The model time or map is not available')
            else:
                embed = discord.Embed(
                    title=f'{model.upper()} MSLP & Precip Gif'
                )
                embed.set_image(url='attachment://gifmap.gif')
                file = discord.File(fp=gif_buffer, filename='gifmap.gif')
                await ctx.followup.send(file=file, embed=embed)

def setup(bot: MonkaMind):
    bot.add_cog(Weather(bot))