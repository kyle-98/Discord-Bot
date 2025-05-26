import random
import requests
from typing import Optional, Callable
from io import BytesIO
from wand.image import Image as WandImage
import discord
from discord.ext import commands
from discord.commands import Option

from bot_config.config import execute_query
from resources.exceptions import NotAdmin

def sot_response(role_id: str) -> str:
    """
    Generate a sot shitpost

    Parameters:
        role_id (str): role of ID of the role the bot should mention when sending the message

    Returns:
        str: shitpost string
    """
    words = ['sot ', 'of ', 'thieves ', 'sea ', 'fotd ', 'the ', 'damned ', 'fof ', 'fort ', 'fortune ', 'thievers ']
    str = f'<{role_id}> are any of you guys looking to play some '
    for i in range(50):
        str += random.choice(words)
    return str

def edit_image(url: str, func: Callable[[WandImage], BytesIO]) -> None:
    """
    Fetch an image from a request and pass the image into a function

    Parameters:
        url (str): url to the image
        func (Callable[[WandImage], BytesIO]): function that takes in an Image object
    """
    if "https://" in url and ".gif" not in url:
        response = requests.get(url)
        response.raise_for_status()

        return func(WandImage(blob=response.content))
    else:
        raise ValueError('Invalid or unsupported image')
    
def magik(image: WandImage) -> BytesIO:
    """
    Distort an image using liquid rescale effects

    Parameters:
        image (wand.image.Image): An image stored in memory

    Returns:
        BytesIO: Converted image to bytes
    """
    image.format = "jpg"
    image.liquid_rescale(
        width=int(image.width * 0.5),
        height=int(image.height * 0.5),
        delta_x=int(0.5 * 2),
        rigidity=0
    )

    buffer = BytesIO()
    image.save(file=buffer)
    buffer.seek(0)
    return buffer


async def find_recent_image_url(ctx: discord.ApplicationContext, lookback: int = 25) -> str | None:
    """
    Find the most recent image sent in a channel looking back n number of messages

    Parameters:
        ctx (discord.ApplicationContext): Context in which the command was invoked
        lookback (int): number of messages to look back, default is 25

    Returns:
        Optional str: If an image was found within the lookback message limit, the url of the image is returned
    """
    async for message in ctx.channel.history(limit=lookback):
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith("image/") and not attachment.filename.endswith(".gif"):
                return attachment.url

        if "https://" in message.content:
            image_extensions = (".jpg", ".jpeg", ".png", ".webp")
            words = message.content.split()
            for word in words:
                if word.startswith("https://") and word.lower().endswith(image_extensions):
                    return word
    return None


def is_admin():
    """
    Slash command decorator to determine is a user is an administrator of the bot or not
    """
    async def predicate(ctx: discord.ApplicationContext):
        """
        Check if the user invoking a slash command defined with the is_admin decorator has their user id listed in the ADMINS table in the config database

        Parameters:
            ctx (discord.ApplicationContext): Context in which the command was invoked
        """
        user_id = str(ctx.author.id)
        print(user_id)
        result = execute_query(
            config_connection=ctx.bot.config_db,
            query='SELECT 1 FROM ADMINS WHERE USER_ID = ?',
            params=(user_id,),
            fetch_one=True
        )
        if result == None:
            print(f'Failed to get admin status of user: {user_id}')
            raise NotAdmin(f'Failed to get admin status of user: {user_id}')
        elif len(result) == 0:
            raise NotAdmin(f'The user: {user_id} is not an administrator')
        else:
            return True
    return commands.check(predicate)