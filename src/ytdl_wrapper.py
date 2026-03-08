import asyncio

import yt_dlp as youtube_dl
import discord

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""

# elif message.content.startswith("!play "):
#         if message.guild.voice_client is None:
#             await message.channel.send("接続していません。")
#             return
#         # 再生中の場合は再生しない
#         if message.guild.voice_client.is_playing():
#             await message.channel.send("再生中です。")
#             return

#         url = message.content[6:]
#         # youtubeから音楽をダウンロードする
#         player = await YTDLSource.from_url(url, loop=client.loop)

#         # 再生する
#         await message.guild.voice_client.play(player)

#         await message.channel.send('{} を再生します。'.format(player.title))

#     elif message.content == "!stop":
#         if message.guild.voice_client is None:
#             await message.channel.send("接続していません。")
#             return

#         # 再生中ではない場合は実行しない
#         if not message.guild.voice_client.is_playing():
#             await message.channel.send("再生していません。")
#             return

#         message.guild.voice_client.stop()

#         await message.channel.send("ストップしました。")


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
