import discord
from discord.ext import commands
from discord.commands import Option
from yt_dlp import YoutubeDL
from io import BytesIO

from resources.helper_funcs import *
from monkamind import MonkaMind


class YoutubeDownloader(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description='Download a youtube video (Video cannot be larger than 200MB)')
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def download_video(self, ctx: discord.ApplicationContext, url = Option(str, "Youtube Video URL", required=True)) -> None:
        """
        Command to allow a user to provide a youtube video url and have the bot download the video into BytesIO in a memory buffer to then upload to catbox.
        This command only allows the user to download videos > 200 MB as this is a limit put in place by catbox.

        Parameters:
            self (commands.Bot): The bot user
            ctx (discord.ApplicationContext): The context in which the command was invoked
            url (discord.Option): The url to the youtube video the user is attempting to download
        """
        await ctx.defer()

        buffer = BytesIO()
        filename = "video.mp4"
        MAX_SIZE = 200 * 1024 * 1024

        ydl_opts = {
            "format": "mp4",
            "quiet": True,
            "outtmpl": "-",
            "noplaylist": True,
            "merge_output_format": "mp4",
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                stream_url = info.get("url")
                filesize = info.get("filesize") or info.get("filesize_approx") or 0

                if filesize > MAX_SIZE:
                    await ctx.respond(f"<:dios_mio:1398894516722860072> Video filesize is too large ({filesize / (1024 * 1024):.2f} MB). Max allowed size is 200 MB.")
                    return

                if not stream_url:
                    await ctx.respond("<:gigi_mood_down:1398894022772133968> Failed to fetch stream URL.")
                    return

                response = requests.get(stream_url, stream=True)
                total_size = 0
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        break
                    total_size += len(chunk)
                    if total_size > MAX_SIZE:
                        await ctx.respond("<:dios_mio:1398894516722860072> Video exceeded 200 MB during download, aborting.")
                        return
                    buffer.write(chunk)

            buffer.seek(0)

            files = {'fileToUpload': (filename, buffer)}
            data = {
                'reqtype': 'fileupload',
                'litterbox': '24'
            }

            resp = requests.post('https://catbox.moe/user/api.php', files=files, data=data)

            if resp.ok:
                litterbox_link = resp.text.strip()
                await ctx.respond(f"<:gigi_mood_up:1398894081119092786> Your video is ready:\n{litterbox_link} (expires in ~24h)")
            else:
                await ctx.respond(f"<:gigi_mood_down:1398894022772133968> Upload failed. Status code: {resp.status_code}")

        except Exception as e:
            await ctx.respond(f"<:gigi_mood_down:1398894022772133968> Unexpected error: {str(e)}")

def setup(bot: MonkaMind):
    bot.add_cog(YoutubeDownloader(bot))