import discord
import asyncio

from youtube_dl import YoutubeDL
from functools import partial
from discord.ext import commands
from ._music_utils_config import ytdl_options

ytdl = YoutubeDL(ytdl_options)


class YTDLSource(discord.PCMVolumeTransformer):
    """
    Contains functionality/data relating to the YouTube download source.
    """

    def __init__(self, source, *, data, requester):
        super().__init__(source)

        self.requester = requester
        self.title = data.get("title")
        self.web_url = data.get("webpage_url")

    def __getitem__(self, item: str):
        return self.__getattribute__(item)

    @classmethod
    async def create_source(
        cls,
        ctx: commands.Context,
        search: str,
        *,
        loop: asyncio.AbstractEventLoop,
        download=False,
    ):
        """
        Creates a source.
        """
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if "entries" in data:  # Get the first item in a playlist
            data = data["entries"][0]

        embed = discord.Embed(
            title=f"🎧 Song Added to the Queue", description=f'🎹 {data["title"]}'
        )

        await ctx.send(embed=embed)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {
                "webpage_url": data["webpage_url"],
                "requester": ctx.author,
                "title": data["title"],
            }

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data: dict, *, loop: asyncio.AbstractEventLoop):
        """
        Used to prepare a stream instead of downloading.
        """
        loop = loop or asyncio.get_event_loop()
        requester = data["requester"]

        to_run = partial(ytdl.extract_info, url=data["webpage_url"], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data["url"]), data=data, requester=requester)
