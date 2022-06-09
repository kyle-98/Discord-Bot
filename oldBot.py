import discord
import random
from discord.ext import commands
from wand.image import Image
import wand, wand.image
import requests
import json


########################################
#			Functions				   #
########################################
def magik(im):
	im.format = "jpg"
	im.liquid_rescale(width=int(im.width * 0.5), height=int(im.height * 0.5), delta_x=int(0.5 * 2), rigidity=0)
	im.save(filename="unknown.jpg")

def requestImage(url):
	r = requests.get(url)
	with open("unknown.jpg", "wb") as outfile:
		outfile.write(r.content)

def sot():
	words = ["sot ", "of ", "thieves ", "sea ", "fotd ", "the ", "damned ", "fof ", "fort ", "fortune ", "thievers "]
	newStr = "are any of you guys looking to play some "
	for i in range(50):
		newStr += random.choice(words)
	return newStr

def editImage(msgC, attach, func):
	if attach:
		attachment = attach[0]
		if ".gif" not in str(attachment):
			requestImage(attachment)
			with Image(filename="unknown.jpg") as im:
				func(im)

	if not attach:
		linkList = msgC.split()
		if "https://" in linkList[1] and ".gif" not in linkList[1]:
			requestImage(linkList[1])
			with Image(filename="unknown.jpg") as im:
				func(im)
				

########################################
#			Bot Class				   #
########################################
class bot(discord.Client):
		
	async def on_ready(self):
		print(f'{self.user} is logged on')
		await self.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name="the sea dogs arena"))

	async def on_message(self, message):
		if message.author == self.user:
			return

		#SOT	
		if message.content.startswith("sot"):
			await message.channel.send(sot())

		#magik old
		"""
		image_types = ["png", "jpeg", "jpg"]
		if message.content.startswith("broken"):
			for attachment in message.attachments:
				if any(attachment.filename.lower().endswith(image) for image in image_types):
					
					#for jpegs
					if attachment.filename.lower().endswith("jpeg"):
						fn = "unknown." + attachment.filename[len(attachment.filename) - 4:]
						await attachment.save(fn)

						with Image(filename=fn) as im:
							magik(im)
							await message.channel.send(file=discord.File("unknown.jpg"))
					
					#For png & jpg
					else:
						fn = "unknown." + attachment.filename[len(attachment.filename) - 3:]
						await attachment.save(fn)

						with Image(filename=fn) as im:	
							magik(im)
							await message.channel.send(file=discord.File("unknown.jpg"))
		"""

		#magik
		if message.content.startswith("!magik"):
			attach, msgC = message.attachments, message.content
			editImage(msgC, attach, magik)
			await message.channel.send(file=discord.File("unknown.jpg"))

#get token from json file					
with open("config.json") as jFile:
	data = json.load(jFile)
	token = data["TOKEN"]		


b = bot()
b.run(token)
