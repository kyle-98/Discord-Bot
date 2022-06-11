import json
import random
import re
from datetime import datetime
from pydoc import describe

import discord
import requests
import wand
import wand.image
from discord.ext import commands
from discord.ui import Button, View
from paginator import NavigationType, Page, Paginator
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
    filePathofBot = data["FILE_PATH_BOT"]

#get image links from file
with open("reactionList.txt") as imageFile:
    reactList = [line.rstrip("\n") for line in imageFile]
    for i in range(len(reactList)):
        reactList[i] = reactList[i].split(" |")[0]

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

@bot.event
async def on_command_error(ctx, error):
    #if isinstance(error, commands.CommandOnCooldown):
    await ctx.send(f"{round(error.retry_after, 2)} seconds left")

#####################
#   Auto Reactions  #
#####################
@bot.event
async def on_message(message):
    msg = message.content
    msgC = message.channel
    if message.author == bot.user:
        pass
    if msg == "patrick":
        await msgC.send(reactList[0])
    if msg == "god":
        await msgC.send(reactList[1])
    if msg == "unit":
        await msgC.send(reactList[2])
    if msg == "legend":
        await msgC.send(reactList[3])
    if msg == "wot":
        await msgC.send(reactList[4])
    if msg == "hugo":
        await msgC.send(reactList[5])
    if msg == "snow":
        await msgC.send(reactList[6])
    if msg == "chungus":
        await msgC.send(reactList[7])
    if msg == "me":
        await msgC.send(reactList[8])
    if msg == "F":
        await msgC.send(reactList[9])
    if msg == "poggers":
        await msgC.send(reactList[10])
    if msg == "dallas":
        await msgC.send(reactList[11])
    if msg == "ibm":
        await msgC.send(reactList[12])
    if msg == "stooge":
        await msgC.send(reactList[13])
    if msg == "help":
        await msgC.send(reactList[14])
    if msg == "sinkies":
        await msgC.send(reactList[15])
    if msg == "chess":
        await msgC.send(reactList[16])
    if msg == "mercy":
        await msgC.send(reactList[17])
    if msg == "ma":
        await msgC.send(reactList[18])
    if msg == "who":
        await msgC.send(reactList[19])
    if msg == "hitreg":
        await msgC.send(reactList[20])
    if msg == "source code":
        await msgC.send(reactList[21])
    if msg == "pace22":
        await msgC.send(reactList[22])
    if msg == "burnt pizza":
        await msgC.send(reactList[23])

#####################
#   Bot Commands    #
#####################

#SOT Command
@bot.command(description="sot of thieves")
@commands.cooldown(1, 60, commands.BucketType.user)
async def sot(ctx):
    await ctx.respond(sotResponse())

#Magik Command
@bot.command(description="magik and image")
@commands.cooldown(1, 5, commands.BucketType.user)
async def magik(ctx, message):
    editImage(message, imageMagik)
    await ctx.respond(file=discord.File("unknown.jpg"))

#Room Temp Command
@bot.command(description="Am I dying in fire rn?")
@commands.cooldown(1, 15, commands.BucketType.user)
async def roomtemp(ctx):
    embed = discord.Embed(
       title = f"Temp Inside Sadge",
       description = getRoomTemp(),
       timestamp = datetime.now() 
    )
    file = discord.File(f"{filePathofBot}/roomTempImage.jpg", filename="roomTempImage.jpg")
    embed.set_image(url="attachment://roomTempImage.jpg")
    await ctx.respond(file=file, embed=embed)

#Weather of any City Command
@bot.command(description="Get weather of a city")
@commands.cooldown(1, 15, commands.BucketType.user)
async def weather(ctx, city):
    embed = discord.Embed(
        title = f"Weather for {city}",
        description = getWeather(city),
        timestamp = datetime.now()
    )
    await ctx.respond(embed=embed)

#MW3 Server List Command
@bot.command(descrption="MW3 Server List")
async def mw3servers(ctx):
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
    await paginator.send(ctx.channel, pages, type=NavigationType.Buttons)

#Start Bot With Token
bot.run(token)
