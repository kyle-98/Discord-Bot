import json
from pydoc import describe
import random
import os
import re
from datetime import datetime

import discord
import asyncio
import requests
import wand
import wand.image
from discord.ext import commands
from discord.ui import Button, View
from discord import Embed
from discord.commands import Option
from paginator import Paginator, Page
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

#Initialize Bot
bot = discord.Bot(debug_guilds=[guildID], intents=discord.Intents.all())
paginator = Paginator(bot)

#################
#   Bot Events  #
#################
@bot.event
async def on_ready():
    print(f'{bot.user} logged into the mainframe')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name="the sea dogs arena"))

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
@bot.command(description="sot of thieves")
@commands.cooldown(1, 60, commands.BucketType.user)
async def sot(ctx):
    await ctx.respond(sotResponse())

#Magik Command
@bot.slash_command(description="magik and image")
@commands.cooldown(1, 5, commands.BucketType.user)
async def magik(ctx, message: Option(str, "Enter a URL", required=False, default='')):
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
@bot.slash_command(description="Am I dying in fire rn?")
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
@bot.slash_command(description="Get weather of a city")
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

#MW3 Server List Command
@bot.slash_command(description="MW3 Server List")
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
        a = Page(embed=discord.Embed(
            title = s[0],
            description = f"""Map: {s[1]}
            Player Count: {s[2]}
            Players:\n
            {nl.join(namesList)}
            """
        ))
        pages.append(a)
    await ctx.followup.send("📈")
    await paginator.send(ctx.channel, pages, type=2, author=ctx.author, disable_on_timeout=False)

#Rocket launch info command
@bot.slash_command(description="Displays Upcoming Rocket Launches")
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
        p = Page(embed=e)
        pages.append(p)
    await ctx.followup.send("🚀")
    await paginator.send(ctx.channel, pages, type=2, author=ctx.author, disable_on_timeout=False)

#Clock in command
@bot.slash_command(description="Is it clock in time?")
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
@bot.slash_command(description="Get the leaderboards for clock in times")
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
@bot.slash_command(descrition="Set a user's times clocked in")
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
@bot.slash_command(description="Pin a message in the pins channel")
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
                await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n**File Name: *{msg.attachments[0].url.split('/')[-1]}***\n{msg.attachments[0].url}")
            else:
                await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n__Message:__ {msg.content}\n**File Name: *{msg.attachments[0].url.split('/')[-1]}***\n{msg.attachments[0].url}")
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
    await ctx.send("message pinned")

#Context menu pin option
@bot.message_command(name="Pin Message")
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
                await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n**File Name: *{msg.attachments[0].url.split('/')[-1]}***\n{msg.attachments[0].url}")
            else:
                await bot.get_channel(pin_channel_id).send(f"**__Message by: {str(msg.author)[:-2]}__**\n{msg.jump_url}\n__Message:__ {msg.content}\n**File Name: *{msg.attachments[0].url.split('/')[-1]}***\n{msg.attachments[0].url}")
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
    await ctx.send("message pinned")
    
#Display error to user
@bot.event
async def on_application_command_error(ctx, error):
    await ctx.defer(ephemeral=True)
    await ctx.followup.send(error)


#Start Bot With Token
bot.run(token)
