import discord
import asyncio
import re
from collections import deque
from typing import Dict, TypedDict, List, Optional, Tuple, Deque
from yomiage.voicebox import VoiceBox
from ytdl_wrapper import YTDLSource

# --- DB定義 ---
class server_setting(TypedDict):
    read_channel: Optional[int]

class user_setting(TypedDict):
    speaker_id: int
    speaker_name: str
    speed: float

class DictDB(TypedDict):
    server_settings: Dict[int, server_setting]
    user_settings: Dict[int, user_setting]

dict_db: DictDB = {
    "server_settings": {},
    "user_settings": {}
}

voice_queues: Dict[int, Deque[Tuple[str, str, float]]] = {}
processing_queues: Dict[int, bool] = {}
voicevox = VoiceBox()

def setup(tree: discord.app_commands.CommandTree, client: discord.Client):
    # --- コマンド・イベント登録 ---
    # /set_read_channel
    @tree.command(
        name="set_read_channel",
        description="現在のテキストチャンネルを読み上げ対象に設定します。"
    )
    async def set_read_channel(ctx: discord.Interaction):
        if ctx.channel is None:
            await ctx.response.send_message("チャンネルが見つかりませんでした。")
            return
        elif ctx.channel.type != discord.ChannelType.text:
            await ctx.response.send_message("テキストチャンネルではありません。")
            return
        elif ctx.channel.guild is None:
            await ctx.response.send_message("サーバーが見つかりませんでした。")
            return
        elif ctx.channel.guild.id not in dict_db["server_settings"]:
            dict_db["server_settings"][ctx.channel.guild.id] = {"read_channel": ctx.channel.id}
        else:
            dict_db["server_settings"][ctx.channel.guild.id]["read_channel"] = ctx.channel.id
        await ctx.response.send_message(f"テキストチャンネル {ctx.channel.name} を読み上げ対象に設定しました。")

    # /unset_read_channel
    @tree.command(
        name="unset_read_channel",
        description="現在のテキストチャンネルを読み上げ対象から外します。"
    )
    async def unset_read_channel(ctx: discord.Interaction):
        if ctx.channel is None:
            await ctx.response.send_message("チャンネルが見つかりませんでした。")
            return
        elif ctx.channel.type != discord.ChannelType.text:
            await ctx.response.send_message("テキストチャンネルではありません。")
            return
        elif ctx.channel.guild is None:
            await ctx.response.send_message("サーバーが見つかりませんでした。")
            return
        elif ctx.channel.guild.id not in dict_db["server_settings"]:
            await ctx.response.send_message("読み上げ対象に設定されていません。")
            return
        elif dict_db["server_settings"][ctx.channel.guild.id]["read_channel"] != ctx.channel.id:
            await ctx.response.send_message("読み上げ対象に設定されていません。")
            return
        dict_db["server_settings"][ctx.channel.guild.id]["read_channel"] = None
        await ctx.response.send_message(f"テキストチャンネル {ctx.channel.name} を読み上げ対象から外しました。")

    # /join
    @tree.command(
        name="join",
        description="現在のボイスチャンネルに接続します。"
    )
    async def join(ctx: discord.Interaction):
        if ctx.user.voice is None:
            await ctx.response.send_message("あなたはボイスチャンネルに接続していません。")
            return
        elif ctx.guild.voice_client is not None:
            if ctx.guild.voice_client.channel == ctx.user.voice.channel:
                await ctx.response.send_message("すでに接続しています。")
                return
        await ctx.user.voice.channel.connect()
        if ctx.channel.guild.id not in dict_db["server_settings"]:
            dict_db["server_settings"][ctx.channel.guild.id] = {"read_channel": ctx.channel.id}
        else:
            dict_db["server_settings"][ctx.channel.guild.id]["read_channel"] = ctx.channel.id
        await ctx.response.send_message(f"接続しました。テキストチャンネル <#{ctx.channel.id}> を読み上げ対象に設定しました。")

    # /leave
    @tree.command(
        name="leave",
        description="ボイスチャンネルから切断します。"
    )
    async def leave(ctx: discord.Interaction):
        if ctx.guild.voice_client is None:
            await ctx.response.send_message("接続していません。")
            return
        await ctx.guild.voice_client.disconnect()
        await ctx.response.send_message("切断しました。")

    async def autocomplete_style(
        ctx: discord.Interaction,
        current: str,
    ) -> list[discord.app_commands.Choice[str]]:
        speaker_name = dict_db["user_settings"].get(ctx.user.id, {}).get("speaker_name", "ずんだもん")
        style_list = voicevox.get_style_list(speaker_name)
        return [
            discord.app_commands.Choice(name=style["name"], value=style["name"])
                for style in style_list
        ]

    # /set_voice
    @tree.command(
        name="set_voice",
        description="音声を設定します。"
    )
    @discord.app_commands.choices(
        speaker=voicevox.build_speaker_choices()[0:25]
    )
    async def set_voice(ctx: discord.Interaction, speaker: str):
        speaker_name = speaker
        speaker_id = voicevox.get_speaker_id(speaker_name)
        if ctx.user.id in dict_db["user_settings"]:
            dict_db["user_settings"][ctx.user.id]["speaker_name"] = speaker_name
            dict_db["user_settings"][ctx.user.id]["speaker_id"] = speaker_id
        else:
            dict_db["user_settings"][ctx.user.id] = {"speaker_name": speaker_name, "speaker_id": speaker_id}
        await ctx.response.send_message(f"音声を {speaker_name}({voicevox.get_speaker_style_name(speaker_id)}) に設定しました。")

    # /set_voice_style
    @tree.command(
        name="set_voice_style",
        description="声色を設定します。"
    )
    @discord.app_commands.autocomplete(
        style=autocomplete_style
    )
    async def set_voice_style(ctx: discord.Interaction, style: str):
        speaker_name = dict_db["user_settings"].get(ctx.user.id, {}).get("speaker_name", "ずんだもん")
        speaker_id = voicevox.get_speaker_id(speaker_name, style) or 3
        if ctx.user.id in dict_db["user_settings"]:
            dict_db["user_settings"][ctx.user.id]["speaker_id"] = speaker_id
        else:
            dict_db["user_settings"][ctx.user.id] = {"speaker_id": speaker_id}
        if "speaker_name" not in dict_db["user_settings"][ctx.user.id]:
            dict_db["user_settings"][ctx.user.id]["speaker_name"] = "ずんだもん"
        await ctx.response.send_message(f"声色を {dict_db['user_settings'][ctx.user.id]['speaker_name']}({voicevox.get_speaker_style_name(speaker_id)}) に設定しました。")

    # /set_speed
    @tree.command(
        name="set_speed",
        description="読み上げ速度を設定します。"
    )
    @discord.app_commands.describe(speed="読み上げ速度を設定します。デフォルト値は1.0です。")
    async def set_speed(ctx: discord.Interaction, speed: discord.app_commands.Range[float, 0.1, 3.0]):
        if ctx.user.id in dict_db["user_settings"]:
            dict_db["user_settings"][ctx.user.id]["speed"] = speed
        else:
            dict_db["user_settings"][ctx.user.id] = {"speed": speed}
        await ctx.response.send_message(f"読み上げ速度を {speed} に設定しました。")

    # 音声の再生のキュー処理関数
    async def process_voice_queue(guild_id: int):
        if processing_queues.get(guild_id, False):
            return
        processing_queues[guild_id] = True
        guild = client.get_guild(guild_id)
        if not guild or not guild.voice_client:
            if guild_id in voice_queues:
                voice_queues[guild_id].clear()
            processing_queues[guild_id] = False
            return
        voice_client = guild.voice_client
        try:
            while guild_id in voice_queues and voice_queues[guild_id]:
                if not voice_client.is_connected():
                    break
                if voice_client.is_playing():
                    await asyncio.sleep(0.5)
                    continue
                message_content, speaker_id, speak_speed = voice_queues[guild_id].popleft()
                wav_data = voicevox.get_voice(message_content, speaker_id=speaker_id, speak_speed=speak_speed)
                voice_client.play(discord.FFmpegPCMAudio(wav_data, **VoiceBox.ffmpeg_options))
        except Exception as e:
            print(f"キュー処理中にエラーが発生しました: {e}")
        finally:
            processing_queues[guild_id] = False

    @client.event
    async def on_message(message):
        server = message.channel.guild
        author = message.author
        channel = message.channel
        try:
            if author == client.user:
                return
            if message.guild.voice_client is None:
                return
            if server.id not in dict_db["server_settings"]:
                return
            if channel.id != dict_db["server_settings"][int(server.id)]["read_channel"]:
                return
            content = message.content
            content = content.replace("\n", " ")
            content = re.sub(r'[^\w\s]', '', content)
            content = content.replace("゛", "")
            content = content.replace("゜", "")
            if "おちんほ" in content:
                content = content.replace("おちんほ", "おちんぽ")
            content = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+', 'URL省略', content)
            if len(content) > 100:
                content = content[:100] + "以下省略"
            speaker_id = dict_db["user_settings"].get(author.id, {}).get("speaker_id", 3)
            speak_speed = dict_db["user_settings"].get(author.id, {}).get("speed", 1.0)
            guild_id = message.guild.id
            if guild_id not in voice_queues:
                voice_queues[guild_id] = deque()
            voice_queues[guild_id].append((content, speaker_id, speak_speed))
            asyncio.create_task(process_voice_queue(guild_id))
        except Exception as e:
            print(e)
            await channel.send("エラーが発生しました。")

    @client.event
    async def on_voice_state_update(member, before, after):
        if member.guild.voice_client is not None:
            if before.channel == member.guild.voice_client.channel and after.channel is not before.channel:
                if member.guild.voice_client is not None and len(member.guild.voice_client.channel.members) == 1:
                    await member.guild.voice_client.disconnect()
                    read_channel_id = dict_db["server_settings"].get(member.guild.id, {}).get("read_channel")
                    if read_channel_id:
                        read_channel = member.guild.get_channel(read_channel_id)
                        if read_channel:
                            await read_channel.send("全員が退出したため、切断しました。")
                            return
                    await member.guild.text_channels[0].send("全員が退出したため、切断しました。")
