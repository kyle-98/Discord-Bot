import json
import random
import os
import re
from datetime import datetime
import random
from tropycal import utils, realtime, tracks
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
from geopy.geocoders import Nominatim
from io import BytesIO
from PIL import Image as im
from pytube import YouTube as YT

import discord
import asyncio
import requests
import subprocess
import wand
import wand.image
from discord.ext import commands
from discord.ui import Button, View
from discord import Embed
from discord import option
from discord.ext.pages import Paginator, Page
from wand.image import Image

#get things from config
with open("config.json") as jFile:
    data = json.load(jFile)
    token = data["TOKEN"]
    guildID = data["GUILD_ID"]
    myWeatherApiKey = data["MY_WEATHER_API_KEY"]
    myWeatherMacAddress = data["MY_WEATHER_MAC_ADDRESS"]
    myWeatherAppKey = data["MY_WEATHER_APPLICATION_KEY"]
    genWeatherApiKey = data["GENERAL_WEATHER_API_KEY"]
    pin_channel_id = data["PIN_CHANNEL_ID"]
    geopy_username = data["GEOPY_USERNAME"]

#get image links from file
with open('reactionList.txt', 'r') as imageFile:
    reactionList = {}
    for line in imageFile:
        temp_reply = line.rstrip('\n').split(' | ')
        reactionList[temp_reply[1]] = temp_reply[0]

#################
#   Functions   #
#################

def sotResponse():
    words = ["sot ", "of ", "thieves ", "sea ", "fotd ", "the ", "damned ", "fof ", "fort ", "fortune ", "thievers "]
    str = "<@&953773735750565978> are any of you guys looking to play some "
    for i in range(50):
        str += random.choice(words)
    return str

def imageMagik(im):
    im.format = "jpg"
    im.liquid_rescale(width=int(im.width * 0.5), height=int(im.height * 0.5), delta_x=int(0.5 * 2), rigidity=0)
    im.save(filename="unknown.jpg")

def requestImage(url):
    response = requests.get(url)
    with open("unknown.jpg", "wb") as outfile:
        outfile.write(response.content)

def editImage(msgC, func):
    if "https://" in msgC and ".gif" not in msgC:
        requestImage(msgC)
        with Image(filename="unknown.jpg") as im:
            func(im)

def getRoomTemp():
    weatherURL = f"https://rt.ambientweather.net/v1/devices/{myWeatherMacAddress}?apiKey={myWeatherApiKey}&applicationKey={myWeatherAppKey}&limit=1"
    response = requests.get(weatherURL)
    data = response.json()
    if response.status_code == 200:
        tempInside = data[0]["tempinf"]
        feelsLikeInside = data[0]["feelsLikein"]
        degreeSymbol = u'\N{DEGREE SIGN}'
        return(f""" 
                Temperature Inside: {tempInside}{degreeSymbol}
                Feels Like Inside: {feelsLikeInside}{degreeSymbol}
                """)
    else:
        return(f"Error Code: {data['cod']} | Error Message: {data['message']}")

def timeFormat(u):
    localTime = datetime.utcfromtimestamp(u)
    return(localTime.time())

def getWeather(city):
    weatherURL = f"https://api.openweathermap.org/data/2.5/weather?q={city}&APPID={genWeatherApiKey}"
    response = requests.get(weatherURL)
    data = response.json()
    if response.status_code == 200:
        KELVIN = 273.13
        temp = int((data["main"]["temp"] - KELVIN) * (9 / 5) +32)
        feelsLikeTemp = int((data["main"]["feels_like"] -  KELVIN) * (9 / 5) + 32)
        pressure = data["main"]["pressure"]
        humidity = data["main"]["humidity"]
        windSpeed = data["wind"]["speed"] * 3.6
        clouds = data["clouds"]["all"]
        timezone = data["timezone"]
        sunrise = timeFormat((data["sys"]["sunrise"]) + timezone)
        sunset = timeFormat((data["sys"]["sunset"]) + timezone)
        description = data["weather"][0]["description"]
        degreeSymbol = u'\N{DEGREE SIGN}'

        return(f"""
                Temp: {temp}{degreeSymbol}
                Feels Like: {feelsLikeTemp}{degreeSymbol}
                Pressure: {pressure} hPa
                Humidity: {humidity}%
                Wind Speed: {round(windSpeed, 2)} mph
                Cloud Cover: {clouds}%
                Sunrise Time: {sunrise}
                Sunset Time: {sunset}
                Information: {description}
                """)
    else:
        return(f"Error for {city} | Error code: {data['cod']} | Error Message: {data['message']}")

#get lat and long from a US ONLY city based on city name
def get_latlong(loc):
    geolocator = Nominatim(user_agent=geopy_username)
    location = geolocator.geocode(loc)
    return (location.latitude, location.longitude)

#return noaa api information about the city
def get_location_info(location):
    response = requests.get(f'https://api.weather.gov/points/{location[0]},{location[1]}')
    data = response.json()
    forecast_link = data['properties']['forecast']
    hours_forecast_link = data['properties']['forecastHourly']
    location_info = [data['properties']['relativeLocation']['properties']['city'], data['properties']['relativeLocation']['properties']['state']]
    return [forecast_link, hours_forecast_link, location_info]

#return data from noaa api dealing with the two-part daily forecast
def get_forecast_data(fl):
    response = requests.get(fl)
    data = response.json()
    periods = []
    for i in data['properties']['periods']:
        periods.append(i)
    return periods

#Check if a date is valid
def check_date(date):
    try:
        datetime.strptime(date, '%Y-%m-%d')
        return True
    except ValueError:
        return False



#Initialize Bot
bot = discord.Bot(intents=discord.Intents.all())

#################
#   Bot Events  #
#################
@bot.event
async def on_ready():
    print(f'{bot.user} logged into the mainframe')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="vtubers"))

#####################
#   Auto Reactions  #
#####################
@bot.event
async def on_message(message):
    msg = message.content
    msgC = message.channel
    if message.author == bot.user:
        pass
    if msg in reactionList:
        await msgC.send(reactionList[msg])

#####################
#   Bot Commands    #
#####################

#SOT Command
@bot.command(description="sot of thieves", integration_types={discord.IntegrationType.guild_install})
@commands.cooldown(1, 60, commands.BucketType.user)
async def sot(ctx):
    await ctx.respond(sotResponse())

#Magik Command
@bot.slash_command(description="magik and image", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 5, commands.BucketType.user)
@option('message', description="Enter a URL", default='')
async def magik(ctx, message):
    await ctx.defer()
    await asyncio.sleep(5)
    if message: 
        editImage(message, imageMagik)
        await ctx.respond(file=discord.File("unknown.jpg"))
    else:
        message = await ctx.channel.history(limit=2).flatten()
        if message[1].attachments:
            attach = message[1].attachments[0]
            editImage(attach.url, imageMagik)
            await ctx.respond(file=discord.File("unknown.jpg"))
        elif message[1].content.startswith("https://"):
            editImage(message[1].content, imageMagik)
            await ctx.respond(file=discord.File("unknown.jpg"))
        else:
            await ctx.respond("No Images Found")
    

#Room Temp Command
@bot.slash_command(description="Am I dying in fire rn?", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 15, commands.BucketType.user)
async def roomtemp(ctx):
    await ctx.defer()
    await asyncio.sleep(3)
    embed = discord.Embed(
       title = f"Temp Inside Sadge",
       description = getRoomTemp(),
       timestamp = datetime.now() 
    )
    file = discord.File(os.getcwd()+"\\roomTempImage.jpg", filename="roomTempImage.jpg")
    embed.set_image(url="attachment://roomTempImage.jpg")
    await ctx.respond(file=file, embed=embed)

#Weather of any City Command
@bot.slash_command(description="Get weather of a city", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 15, commands.BucketType.user)
async def weather(ctx, city):
    await ctx.defer()
    await asyncio.sleep(4)
    embed = discord.Embed(
        title = f"Weather for {city}",
        description = getWeather(city),
        timestamp = datetime.now()
    )
    await ctx.respond(embed=embed)

#Weather of any US city
@bot.slash_command(description="Get the weather of any city in the United States ONLY use <city>, <state> for city field", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 10, commands.BucketType.user)
async def weatherforecast(ctx, city):
    pages = []
    location = get_latlong(city)
    location_info = get_location_info(location)
    forecast_data = get_forecast_data(location_info[0])
    for fd in forecast_data:
        precip_prob = fd["probabilityOfPrecipitation"]["value"]
        desc = f"""Temperature: {fd["temperature"]} °F
        Precip Probability: {str(precip_prob) + '%' if precip_prob != None else '0%'}
        Dewpoint: {(fd["dewpoint"]["value"] * (9/5)) + 32} °F
        Humidity: {fd["relativeHumidity"]["value"]}%
        Wind Speed: {fd["windSpeed"]}
        Wind Direction: {fd["windDirection"]}

        Short Desc: {fd["shortForecast"]}

        Detailed Forecast: {fd["detailedForecast"]}
        """
        embed = discord.Embed(
            title = f'Weather for {fd["name"]} in {location_info[2][0]}, {location_info[2][1]}',
            description=desc,
            color = 0xFFC0CB
        )
        embed.set_thumbnail(url=f'{fd["icon"][:-11]}size=large')
        p = Page(embeds=[embed])
        pages.append(p)
    paginator = Paginator(pages=pages, author_check=False)
    #await ctx.respond(content="Weather Forecast:")
    await paginator.respond(ctx.interaction, ephemeral=False)

#MW3 Server List Command
@bot.slash_command(description="MW3 Server List", integration_types={discord.IntegrationType.guild_install})
async def mw3servers(ctx):
    await ctx.defer()
    await asyncio.sleep(5)
    url = "https://plutonium.pw/api/servers"
    response = requests.get(url)
    data = response.json()
    serverList = []
    for d in data:
        if d["game"] == "iw5mp" and len(d["players"]) >= 10:
            sN = d['hostname']
            playersList = []
            newSN = re.sub('\^[0-9]{1}', '', sN)
            for i in range(len(d['players'])):
                playersList.append(d['players'][i]['username'])
            server = []
            server.append(newSN)
            server.append(d['map'])
            server.append(len(d['players']))
            server.append(playersList)

            serverList.append(server)

    serverList = sorted(serverList, key=lambda x:x[2], reverse=True)
    pages = []
    nl = "\n"
    for s in serverList:
        namesList = list(s[3])
        a = Page(embeds=[discord.Embed(
            title = s[0],
            description = f"""Map: {s[1]}
            Player Count: {s[2]}
            Players:\n
            {nl.join(namesList)}
            """
        )])
        pages.append(a)
    paginator = Paginator(pages=pages, author_check=False)
    await paginator.respond(ctx.interaction, ephemeral=False)

#Rocket launch info command
@bot.slash_command(description="Displays Upcoming Rocket Launches", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
async def rocketlaunches(ctx):
    await ctx.defer()
    await asyncio.sleep(5)
    request = requests.get("https://ll.thespacedevs.com/2.2.0/launch/upcoming")
    data = request.json()

    launchesList = []

    for d in data["results"]:
        launchInfo = []

        if d['name']:
            name = d['name']
        else:
            name = "N/A"
        if d['window_start'] and d['window_end']:
            window_start = d['window_start']
            window_end = d['window_end']
        else:
            window_start = "N/A"
            window_end = "N/A"
        if d['probability'] and d['probability'] != -1:
            probability = str(d['probability']) + "%"
        elif d['probability'] and d['probability'] == -1:
            probability = "TBD"
        else:
            probability = "N/A"
        if d['launch_service_provider']['name']:
            provider = d['launch_service_provider']['name']
        else:
            provider = "N/A"
        if d['rocket']['configuration']['full_name']:
            full_name = d['rocket']['configuration']['full_name']
        else:
            full_name = "N/A"
        if d['mission']:
            mission_desc = d['mission']['description']
        else:
            mission_desc = "N/A"
        if d['pad']['name'] and d['pad']['location']['name']:
            pad_name = d['pad']['name']
            pad_loc = d['pad']['location']['name']
        else:
            pad_name = "N/A"
            pad_loc = "N/A"
        map_image = d['pad']['map_image']
        small_image = d['image']

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
    for l in launchesList:
        e = discord.Embed(
            title = l[0],
            description = f"""Provider: {l[1]}
            Rocket: {l[2]}
            Weather Conditions: {l[3]}
            Launch Window: {l[4][0]} - {l[4][1]}

            Mission: {l[6]}  
            """,
            color = 0xf36005
        )
        e.add_field(name=f"Pad: {l[5][0]} | {l[5][1]}", value="\u200B")
        e.set_image(url=l[7])
        e.set_thumbnail(url=l[8])
        p = Page(embeds=[e])
        pages.append(p)
    paginator = Paginator(pages=pages, author_check=False)
    await paginator.respond(ctx.interaction, ephemeral=False)

#Clock in command
@bot.slash_command(description="Is it clock in time?", integration_types={discord.IntegrationType.guild_install})
@commands.cooldown(1, 5, commands.BucketType.user)
async def clockin(ctx):
    TODAYS_DATE = str(datetime.today())[0:10]

    def writeToJson(newData, filename, userID):
        with open(filename, "r+") as file:
            c = 0
            fileData = json.load(file)
            for data in fileData["clockInList"]:
                if data["userID"] == userID:
                    c += 1
                    break
            if c == 0:
                fileData["clockInList"].append(newData)
                file.seek(0)
                json.dump(fileData, file, indent=4)
        file.close()

    def increment(filename, userID):
        with open(filename) as file:
            data = json.load(file)
        for d in data["clockInList"]:
            if d["userID"] == userID and d["lastTimeClocked"] != TODAYS_DATE:
                d["timesClockedIn"] += 1
                d["lastTimeClocked"] = TODAYS_DATE
        file.close()
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        file.close()

    def hasClocked(filename, userID):
        with open(filename) as file:
            data = json.load(file)
            for d in data["clockInList"]:
                if d["userID"] == userID and d["lastTimeClocked"] == TODAYS_DATE:
                    return True
                else:
                    return False

    user = {
        "userID":ctx.author.id,
        "timesClockedIn":0,
        "lastTimeClocked":TODAYS_DATE
    }
    writeToJson(user, os.getcwd()+"\\clockIn.json", ctx.author.id)
    timeNow = datetime.now().strftime("%H:%M:%S")
    hourNow = datetime.now().strftime("%H")
    if hourNow == "01":
        if hasClocked(os.getcwd()+"\\clockIn.json", ctx.author.id):
            await ctx.respond("You have already clocked in for the day.")
        else:
            increment(os.getcwd()+"\\clockIn.json", ctx.author.id)
            await ctx.respond("You have been clocked in.")
    else:
        await ctx.respond(f"Sorry clock in time is at 1 am, good hands time.  Right now the time is: {timeNow}")

#Clock in leaderboard command
@bot.slash_command(description="Get the leaderboards for clock in times", integration_types={discord.IntegrationType.guild_install})
@commands.cooldown(1, 5, commands.BucketType.user)
async def clockinleaderboard(ctx):
    await ctx.defer()
    await asyncio.sleep(2)
    namesList = []
    with open(os.getcwd()+"\\clockIn.json") as file:
        data = json.load(file)
        for d in data["clockInList"]:
            namesList.append((str(bot.get_user(d["userID"])), d["timesClockedIn"]))
    file.close()
    namesList = sorted(namesList, key=lambda x: x[1], reverse=True)
    c = 1
    def buildString(nL):
        textList = []
        c = 1
        for n in nL:
            tempStr = f"Position {c}: {n[0][:-2]} | {n[1]} clock-in's"
            textList.append(tempStr)
            c += 1
        str = '\n'.join(textList)
        return(str)

    embed = discord.Embed(
        title="Top Clock-In Workers",
        description=buildString(namesList),
        timestamp=datetime.now()
    )
    
    await ctx.followup.send("📈")
    await ctx.send(embed=embed)

#Set clockin time for person
@bot.slash_command(descrition="Set a user's times clocked in", integration_types={discord.IntegrationType.guild_install})
@commands.is_owner()
async def setclockin(ctx, user_id, times):
    await ctx.defer(ephemeral=True)
    await asyncio.sleep(1)
    filename = os.getcwd()+"\\clockIn.json"
    user_id = int(user_id)
    times = int(times)

    with open(filename) as file:
        data = json.load(file)
    for d in data["clockInList"]:
        if d["userID"] == user_id:
            d["timesClockedIn"] = times
    file.close()

    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
    file.close()

    await ctx.followup.send(f"Set {str(bot.get_user(user_id))} to {times} times clocked in.")

#pin a message in a channel to bypass 50 pin limit
@bot.slash_command(description="Pin a message in the pins channel", integration_types={discord.IntegrationType.guild_install})
@commands.cooldown(1, 5, commands.BucketType.user)
async def pin(ctx, msg_id):
    msg = await ctx.fetch_message(msg_id)
    response_embed = discord.Embed(
        url=msg.jump_url,
        title=f"Message By {str(msg.author)[:-2]}",
        description=(f"{msg.content}"),
        timestamp=msg.created_at  
    )

    if(len(msg.attachments) > 0):
        if(msg.attachments[0].content_type == None):
            await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n**File Name: *{msg.attachments[0].url.split('/')[-1]}***\n{msg.attachments[0].url}")
        elif(msg.attachments[0].content_type.startswith("application")):
            if(msg.content == ""):
                embed = discord.Embed(
                    url=msg.jump_url,
                    title=f"Message by: {str(msg.author)[:-2]}",
                    description=f"Filename: {msg.attachments[0].url.split('/')[-1]}\n\n[Download Link]({msg.attachments[0].url})",
                    timestamp=msg.created_at
                )
                #await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n**File Name: *{msg.attachments[0].url.split('/')[-1]}***\n{msg.attachments[0].url}")
                await bot.get_channel(pin_channel_id).send(embed=embed)
            else:
                embed = discord.Embed(
                    url=msg.jump_url,
                    title=f"Message by: {str(msg.author)[:-2]}",
                    description=f"__Message:__ {msg.content}\n\n__Filename:__ {msg.attachments[0].url.split('/')[-1]}\n\n[Download Link]({msg.attachments[0].url})",
                    timestamp=msg.created_at
                )
                await bot.get_channel(pin_channel_id).send(embed=embed)
                #await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n__Message:__ {msg.content}\n**File Name: *{msg.attachments[0].url.split('/')[-1]}***\n{msg.attachments[0].url}")  
        elif(msg.attachments[0].content_type.startswith("video")):
            await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n{msg.attachments[0]}")
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
            await bot.get_channel(pin_channel_id).send(embeds=attach_embeds)
    else:
        await bot.get_channel(pin_channel_id).send(embed=response_embed)
    await ctx.respond(f"Message: [Jump to message]({msg.jump_url})\n**Pinned by {str(ctx.author)[:-2]}**")

#Context menu pin option
@bot.message_command(name="Pin Message", integration_types={discord.IntegrationType.guild_install})
async def pin_message(ctx, message: discord.Message):
    msg = await ctx.fetch_message(message.id)
    response_embed = discord.Embed(
        url=msg.jump_url,
        title=f"Message By {str(msg.author)[:-2]}",
        description=(f"{msg.content}"),
        timestamp=msg.created_at  
    )

    if(len(msg.attachments) > 0):
        if(msg.attachments[0].content_type == None):
            await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n**File Name: *{msg.attachments[0].url.split('/')[-1]}***\n{msg.attachments[0].url}")
        elif(msg.attachments[0].content_type.startswith("application")):
            if(msg.content == ""):
                embed = discord.Embed(
                    url=msg.jump_url,
                    title=f"Message by: {str(msg.author)[:-2]}",
                    description=f"Filename: {msg.attachments[0].url.split('/')[-1]}\n\n[Download Link]({msg.attachments[0].url})",
                    timestamp=msg.created_at
                )
                await bot.get_channel(pin_channel_id).send(embed=embed)
            else:
                embed = discord.Embed(
                    url=msg.jump_url,
                    title=f"Message by: {str(msg.author)[:-2]}",
                    description=f"__Message:__ {msg.content}\n\n__Filename:__ {msg.attachments[0].url.split('/')[-1]}\n\n[Download Link]({msg.attachments[0].url})",
                    timestamp=msg.created_at
                )
                await bot.get_channel(pin_channel_id).send(embed=embed)
        elif(msg.attachments[0].content_type.startswith("video")):
            await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n{msg.attachments[0]}")
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
            await bot.get_channel(pin_channel_id).send(embeds=attach_embeds)
    else:
        await bot.get_channel(pin_channel_id).send(embed=response_embed)
    await ctx.respond(f"Message: [Jump to message]({msg.jump_url})\n**Pinned by {str(ctx.author)[:-2]}**")

#Selection menu for CPC outlooks
class CPCOutlookView(discord.ui.View):
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
    async def select_callback(self, select, interaction):
        if select.values[0] == "6 to 10 Day Outlook":
            temp_outlook_embed = discord.Embed(
                url="https://www.cpc.ncep.noaa.gov/products/predictions/610day/",
                title=f"6 to 10 Day Outlook",
                description="6 to 10 Day Outlook from the Climate Prediction Center",
                color=0x3498db
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            temp_outlook_embed.set_image(url=f"https://www.cpc.ncep.noaa.gov/products/predictions/610day/610temp.new.gif{unique_query_param}")

            precip_outlook_embed = discord.Embed(
                url="https://www.cpc.ncep.noaa.gov/products/predictions/610day/"
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            precip_outlook_embed.set_image(url=f"https://www.cpc.ncep.noaa.gov/products/predictions/610day/610prcp.new.gif{unique_query_param}")
            await interaction.response.send_message(embeds=[temp_outlook_embed, precip_outlook_embed])

        elif select.values[0] == "8 to 14 Day Outlook":
            temp_outlook_embed = discord.Embed(
                url="https://www.cpc.ncep.noaa.gov/products/predictions/814day/",
                title=f"8 to 14 Day Outlook",
                description="8 to 14 Day Outlook from the Climate Prediction Center",
                color=0x3498db
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            temp_outlook_embed.set_image(url=f"https://www.cpc.ncep.noaa.gov/products/predictions/814day/814temp.new.gif{unique_query_param}")

            precip_outlook_embed = discord.Embed(
                url="https://www.cpc.ncep.noaa.gov/products/predictions/814day/"
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            precip_outlook_embed.set_image(url=f"https://www.cpc.ncep.noaa.gov/products/predictions/814day/814prcp.new.gif{unique_query_param}")
            await interaction.response.send_message(embeds=[temp_outlook_embed, precip_outlook_embed])

#Send selection prompt for CPC outlooks
@bot.slash_command(description="Get CPC Outlook Maps", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 5, commands.BucketType.user)
async def cpcoutlook(ctx):
    await ctx.respond("Choose an option", view=CPCOutlookView())

#Create a view for select dropdown options
class TropicalView(discord.ui.View):
    @discord.ui.select(
        placeholder = 'Choose an option',
        min_values = 1,
        max_values = 1,
        options = [
            discord.SelectOption(
                label="2-Day Graphical Outlook",
                description="Two-day outlook for tropical weather (AL)"
            ),
            discord.SelectOption(
                label="7-Day Graphical Outlook",
                description="Seven-day outlook for tropical weather (AL)"
            )
        ]
    )
    async def select_callback(self, select, interaction):
        if(select.values[0] == "2-Day Graphical Outlook"):
            embed = discord.Embed(
                url="https://www.nhc.noaa.gov/gtwo.php?basin=atlc&fdays=2",
                title="Atlantic 2-Day Graphical Tropical Weather Outlook"
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            embed.set_image(url=f"https://www.nhc.noaa.gov/xgtwo/two_atl_2d0.png{unique_query_param}")
            await interaction.response.send_message(embed=embed)

        elif(select.values[0] == "7-Day Graphical Outlook"):
            embed = discord.Embed(
                url="https://www.nhc.noaa.gov/gtwo.php?basin=atlc&fdays=7",
                title="Atlantic 7-Day Graphical Tropical Weather Outlook"
            )
            unique_query_param = f'?random={random.randint(1, 1000)}'
            embed.set_image(url=f"https://www.nhc.noaa.gov/xgtwo/two_atl_7d0.png{unique_query_param}")
            await interaction.response.send_message(embed=embed)

#Send TropicalView selection to the user
@bot.slash_command(description="Get NHC Tropical Outlook Maps", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 5, commands.BucketType.user)
async def tropicaloutlook(ctx):
    await ctx.respond("Choose an option", view=TropicalView())

#Generate data before bot starts, store the information in memory until an update command has been run
try:
    storms = realtime.Realtime().list_active_storms(basin='all')
except:
    storms = []
storm_data_datetime = datetime.now()
def update_storm_data():
    global storms
    global storm_data_datetime
    storms = realtime.Realtime().list_active_storms(basin='all')
    storm_data_datetime = datetime.now()

try:
    update_storm_data()
except:
    pass

#generate select menu options for tropicalstorms command
def generate_options():
    #storms = realtime.Realtime().list_active_storms(basin='all')
    selection_options = []
    for s in storms:
        storm = realtime.Realtime().get_storm(s)
        if not storm.invest:
            selection_options.append(discord.SelectOption(
                label=f"{storm.name} | {storm.id}",
                description=f"This storm is located in the {storm.basin}"
            ))
    return selection_options

storm_options = generate_options()

def plot_boundaries(ax):
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidths=0.5, linestyle='solid', edgecolor='k')
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidths=1.0, linestyle='solid', edgecolor='k')
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=1.0, linestyle='solid', edgecolor='k')
    ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#EEEEEE', edgecolor='face')

    return ax


#Create a list of drop downs for the select menu
class TropicalStormDropDown(discord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder=f"Chose a storm",
            min_values=1,
            max_values=1,
            options=options
        )
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("generating... <a:spin:1149889506628096161>")

        user_select = self.values[0].split(' | ')
        storm = realtime.Realtime().get_storm(user_select[1])
        proj = ccrs.PlateCarree()
        fig = plt.figure(figsize=(11,8))
        ax = plt.axes(projection=proj) 
        ax = plot_boundaries(ax)
        # ax.add_feature(cfeature.STATES.with_scale('50m'), linewidths=0.5, linestyle='solid', edgecolor='k')
        # ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidths=1.0, linestyle='solid', edgecolor='k')
        # ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidths=1.0, linestyle='solid', edgecolor='k')
        # ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#EEEEEE', edgecolor='face')
        ax = utils.add_tropycal(ax)
        storm.plot_forecast_realtime(ax=ax)
        center_latlon = [storm.get_forecast_realtime()['lat'][0], storm.get_forecast_realtime()['lon'][0]]
        ax.set_extent([center_latlon[1] - 40, center_latlon[1] + 15, center_latlon[0] + 20, center_latlon[0] - 15])
        
        plt.savefig('x.png')
        plt.show(block=False)
        plt.close("all")
        storm_type = storm.get_forecast_realtime()['type'][0]
        if(storm_type == 'TS'):
            storm_type = 'Tropical Storm'
        elif(storm_type == 'HU'):
            storm_type = 'Hurricane'

        nhc_embed = discord.Embed(
            title=f"NHC Track for {storm_type} {storm.name}"
        )
        file = discord.File('x.png')
        nhc_embed.set_image(url='attachment://x.png')
        await interaction.edit_original_message(content="", file=file, embed=nhc_embed)

#create a view for the select menu (custom class instead of decorator)
class TropicalStormsView(discord.ui.View):
    def __init__(self, options):
        super().__init__()
        self.add_item(TropicalStormDropDown(options))

#Send TCInfoView selection to the user to let them choose a tropical system to plot
@bot.slash_command(description="Get NHC Prediction Plots", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 15, commands.BucketType.user)
async def tropicalstorms(ctx):
    #await ctx.defer()
    options = storm_options
    view = TropicalStormsView(options)
    await ctx.respond(f"This data is {round((datetime.now() - storm_data_datetime).total_seconds() / 60, 2)} minute(s) old.  Use /updatetropicalstorms to refresh it", view=view)

#update tropical storm data with the most recent data from NOAA servers
@bot.slash_command(description="Update the tropical storm data with most recent data", integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 120, commands.BucketType.user)
async def updatetropicalstorms(ctx):
    await ctx.respond(f"Updating... <a:spin:1149889506628096161>")
    update_storm_data()
    message = await ctx.send(content="Generating options... <a:spin:1149889506628096161>")
    global storm_options
    storm_options = generate_options()
    await message.edit(content="All Storm Data is now updated.")

#Generate gif from 64 images from tropical tidbits
def gen_gif_map(base_url, model):
    print('Generating gif...')
    image_links = []
    gif_frames = []
    if len(base_url) == 2:
        if model == 'gdps' or model == 'ecmwf':
            nums = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072', '078', '084', 
            '090', '096', '102', '108', '114', '120', '126', '132', '138', '144', '150', '156', '162', '168', '174', 
            '180', '186', '192', '198', '204', '210', '216', '222', '228', '234', '240']
        else:
            nums = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072', '078', '084', 
                    '090', '096', '102', '108', '114', '120', '126', '132', '138', '144', '150', '156', '162', '168', 
                    '174', '180', '186', '192', '198', '204', '210', '216', '222', '228', '234', '240', '246', '252', 
                    '258', '264', '270', '276', '282', '288', '294', '300', '306', '312', '318', '324', '330', '336', 
                    '342', '348', '354', '360', '366', '372', '378', '384']
        for i in nums:
            image_links.append(f'{base_url[0]}{i}/{base_url[1]}')
    else:
        if model == 'gem':
            for i in range(1, 41):
                image_links.append(f'{base_url[0]}{i}.png')
        else:
            for i in range(1, 65):
                image_links.append(f'{base_url[0]}{i}.png')
    
    check = True
    for link in image_links:
        response = requests.get(link)
        if response.status_code == 404:
            check = False
        else:
            image = im.open(BytesIO(response.content))
            gif_frames.append(image)
            check = True
        if not check:
            break
    if not check:
        print('cancelled gif generation')
        return False
    else:
        gif_frames[0].save('gifmap.gif', format='GIF', append_images=gif_frames[1:], save_all=True, loop=0)
        print('done generating gif')
        return True

#Autocomplete autofill options for precip type based on the model choice
def get_precip_types(ctx: discord.AutocompleteContext):
    model_type = ctx.options['model']
    if model_type == 'ecmwf':
        return ['mslp']
    else:
        return ['mslp', 'snow']

#Autocomplete autofill options for region based on the website choice
def get_regions(ctx: discord.AutocompleteContext):
    site = ctx.options['site']
    if site == 'tropicaltidbits':
        return ['CONUS', 'North-West', 'North-Central', 'North-East', 'Eastern', 'South-West', 'South-Central', 'South-East', 'Western']
    else:
        return ['CONUS', 'North-West', 'North-Central', 'North-East', 'Mid-Atlantic','Sout-West', 'South-Central', 'South-East', 'Mid-West',]

def gen_base_url(site, model, type, time, region, date):
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
        #return gen_gif_map(base_url, model)
    else:
        if model == 'cmc':
            model = 'gdps'
        if model == 'ecmwf':
            model = 'ecmwf_full'
        base_url = [f'https://m1o.pivotalweather.com/maps/models/{model}/{date[0]}{date[1]}{date[2]}{time}/']
        if type == 'mslp':
            if model == 'ecmwf':
                base_url.append(f'prateptype_cat_ecmwf-imp.{pw_dict[region]}.png')
            else:
                base_url.append(f'prateptype_cat-imp.{pw_dict[region]}.png')
        else:
            base_url.append(f'sn10_acc-imp.{pw_dict[region]}.png')
        #return gen_gif_map(base_url, model)
    map_check = gen_gif_map(base_url, model)
    return map_check

#Generate gif based on tropical tidbits or pivotal weather GFS/ECWMF/CMC maps
@bot.slash_command(description='Generate gif based on tropical tidbits or pivotal weather GFS/ECMWF/CMC maps', integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 15, commands.BucketType.user)
@option("site", str, description="Enter source data website", choices=['tropicaltidbits', 'pivotalweather'], required=True)
@option("model", str, description="Weather Model", autocomplete=discord.utils.basic_autocomplete(get_precip_types), required=True)
@option("type", str, choices=['00', '06', '12', '18'], required=True)
@option("time", str, choices=['00', '06', '12', '18'], required=True)
@option("region", str, description='Region of the US', autocomplete=discord.utils.basic_autocomplete(get_regions), required=True)
@option("date", str, description='Use the format: YYYY-MM-DD', required=True)
async def modelgifs(ctx, site: str, model: str, type: str, time: str, region: str, date: str):
    await ctx.defer()
    cd = check_date(date)
    td = date.split('-')
    if not cd:
        await ctx.followup.send('That is not a valid date')
    elif datetime(int(td[0]), int(td[1].lstrip('0')), int(td[2].lstrip('0'))) > datetime.today():
        await ctx.followup.send('You cannot use dates in the future')
    else:
        check = gen_base_url(site, model, type, time, region, td)
        if not check:
            await ctx.followup.send('The model time or map is not available')
        else:
            embed = discord.Embed(
                title=f'{model.upper()} MSLP & Precip Gif'
            )
            embed.set_image(url='attachment://gifmap.gif')
            file = discord.File('gifmap.gif')
            await ctx.followup.send(file=file, embed=embed)

#Check video length
def check_vid_length(url):
    try:
        video = YT(url)
        vl = video.length
        return vl
    except:
        return None
#Download youtube mp3 file
def download_mp3(url):
    video = YT(url)
    audio = video.streams.filter(only_audio=True).first()
    audio.download(output_path=os.getcwd(), filename=f'{audio.title}.mp4')
    return audio.title

#Download youtube video
@bot.slash_command(description='Convert youtube to mp3', integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 15, commands.BucketType.user)
@option("url", str, required= True)
async def youtubetomp3(ctx, url):
    video_check = check_vid_length(url)
    if video_check == None:
        await ctx.respond('Not a valid youtube url')
    elif video_check > 2400:
        await ctx.respond('Video is too long to convert (videos must be less than 40 minutes)')
    else:
        await ctx.defer()
        video_title = download_mp3(url)
        subprocess.run(['ffmpeg', '-i', f'{os.getcwd()}\\{video_title}.mp4', f'{os.getcwd()}\\{video_title}.mp3'])
    file = discord.File(f'{video_title}.mp3')
    await ctx.followup.send(content="Here is your file <a:Chatting:1149889559006560377>",file=file)
    os.remove(f'{os.getcwd()}\\{video_title}.mp4')
    os.remove(f'{os.getcwd()}\\{video_title}.mp3')

#Check if the string format: "YYYY-YYYY" has a valid year range
def check_years(year_str):
    pattern = r'^\d{4}-\d{4}$'
    if re.match(pattern, year_str):
        years = year_str.split('-')
        try:
            year1 = int(years[0])
            year2 = int(years[1])
            datetime(year1, 1, 1)
            datetime(year2, 1, 1)
            if int(year1) < int(year2) and int(year1) >= 1851 and int(year2) <= datetime.now().year:
                return True
            else:
                return False
        except ValueError:
            return False
    else:
        return False


#Image Manipulation
@bot.slash_command(description='Edit images', integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 5, commands.BucketType.user)
@option("action", str, description='Choose edit action', choices=['flip horizontal', 'flip vertical'], required=True)
@option("image_link", str, description='Enter an image URL', required=False, default='')
async def edit_image(ctx, action, image_link):
    try:
        os.remove('unknown.jpg')
    except:
        pass
    await ctx.defer()
    if image_link:
        if not image_link.endswith('.gif'):
            try:
                requestImage(image_link)
            except:
                await ctx.respond('invalid image link')
    else:
        message = await ctx.channel.history(limit=2).flatten()
        if message[1].attachments:
            attach = message[1].attachments[0]
            requestImage(attach.url)
        elif message[1].content.startswith("https://"):
            requestImage(message[1].content)
        else:
            await ctx.respond("No Images Found")
    edited_image = im.open('unknown.jpg')
    if action == 'flip horizontal':
        edited_image = edited_image.transpose(im.FLIP_LEFT_RIGHT)
    else:
        edited_image = edited_image.transpose(im.FLIP_TOP_BOTTOM)
    edited_image.save('unknown.jpg')
    await ctx.respond(file=discord.File("unknown.jpg"))

# Allow user to generate map from city that shows all tropical cyclones that have went near the location
@bot.slash_command(description='Generate map of all tropical cyclones from a given location', integration_types={discord.IntegrationType.guild_install, discord.IntegrationType.user_install})
@commands.cooldown(1, 15, commands.BucketType.user)
@option("location", str, description='Provide: City, STATE(2 letters) or: City, Country', required=True)
@option("radius", int, description='Radius, in km, around point to draw storm tracks', choices=[50, 100, 150], required=True)
@option("dots_or_lines", str, description='Map will have dots or lines for tracks', choices=['dots', 'lines'], required=True)
@option("year_range", str, description='Year range, must be YYYY-YYYY: 1851-2023, oldest year has to be >= 1851', default=None)
async def cyclonehistory(ctx, location, radius, dots_or_lines, year_range):
    proj = ccrs.PlateCarree()
    fig = plt.figure(figsize=(11,8))
    ax = plt.axes(projection=proj) 
    ax = plot_boundaries(ax)
    ax = utils.add_tropycal(ax)
    await ctx.defer()
    basin = tracks.TrackDataset(basin='both', include_btk=True)
    try:
        latlon = get_latlong(location)
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

        plt.savefig('x.png')
        plt.show(block=False)
        plt.close("all")
        loc_split = location.split(', ')
        embed = discord.Embed(
            title=f'TC Tracks within a {radius} km range of {loc_split[0]}, {loc_split[1]}'
        )
        file = discord.File('x.png')
        embed.set_image(url='attachment://x.png')
        await ctx.followup.send(file=file, embed=embed)
    except:
        await ctx.followup.send('An error occured, try again.')
    


#Display error to user
@bot.event
async def on_application_command_error(ctx, error):
    await ctx.defer(ephemeral=True)
    await ctx.followup.send(error)

#Start Bot With Token
bot.run(token)