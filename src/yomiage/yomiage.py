import discord
import asyncio
import re
import io
from collections import deque
from typing import Dict, TypedDict, Optional, Tuple, Deque
from yomiage.voicebox import VoiceBox
from yomiage import database

# --- DB定義 (メモリキャッシュ) ---
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


async def init():
    """データベースを初期化し、設定をメモリにロードする"""
    await database.init_db()
    dict_db["server_settings"] = await database.load_all_server_settings()
    dict_db["user_settings"] = await database.load_all_user_settings()


def preprocess_text(content: str) -> str:
    """メッセージのテキストを読み上げ用に前処理する"""
    # 改行をスペースに変換
    content = content.replace("\n", " ")
    # URLを省略
    content = re.sub(r'https?://\S+', 'URL省略', content)
    # 特殊文字を除去（URLの後に処理）
    content = re.sub(r'[^\w\s\u3000-\u9FFF\uFF00-\uFFEF]', '', content)
    # 濁点・半濁点の除去
    content = content.replace("゛", "")
    content = content.replace("゜", "")
    # 100文字制限
    if len(content) > 100:
        content = content[:100] + "以下省略"
    return content


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
        if ctx.channel.type != discord.ChannelType.text:
            await ctx.response.send_message("テキストチャンネルではありません。")
            return
        if ctx.guild is None:
            await ctx.response.send_message("サーバーが見つかりませんでした。")
            return

        dict_db["server_settings"][ctx.guild.id] = {"read_channel": ctx.channel.id}
        await database.set_server_setting(ctx.guild.id, ctx.channel.id)
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
        if ctx.channel.type != discord.ChannelType.text:
            await ctx.response.send_message("テキストチャンネルではありません。")
            return
        if ctx.guild is None:
            await ctx.response.send_message("サーバーが見つかりませんでした。")
            return

        server = dict_db["server_settings"].get(ctx.guild.id)
        if not server or server.get("read_channel") != ctx.channel.id:
            await ctx.response.send_message("読み上げ対象に設定されていません。")
            return

        dict_db["server_settings"][ctx.guild.id]["read_channel"] = None
        await database.set_server_setting(ctx.guild.id, None)
        await ctx.response.send_message(f"テキストチャンネル {ctx.channel.name} を読み上げ対象から外しました。")

    # /join
    @tree.command(
        name="join",
        description="現在のボイスチャンネルに接続します。"
    )
    async def join(ctx: discord.Interaction):
        await ctx.response.defer()

        if ctx.user.voice is None:
            await ctx.followup.send("あなたはボイスチャンネルに接続していません。")
            return
        if ctx.guild.voice_client is not None:
            if ctx.guild.voice_client.channel == ctx.user.voice.channel:
                await ctx.followup.send("すでに接続しています。")
                return

        await ctx.user.voice.channel.connect()

        dict_db["server_settings"][ctx.guild.id] = {"read_channel": ctx.channel.id}
        await database.set_server_setting(ctx.guild.id, ctx.channel.id)
        await ctx.followup.send(f"接続しました。テキストチャンネル <#{ctx.channel.id}> を読み上げ対象に設定しました。")

    # /leave
    @tree.command(
        name="leave",
        description="ボイスチャンネルから切断します。"
    )
    async def leave(ctx: discord.Interaction):
        await ctx.response.defer()

        if ctx.guild.voice_client is None:
            await ctx.followup.send("接続していません。")
            return

        await ctx.guild.voice_client.disconnect()
        await ctx.followup.send("切断しました。")

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
        await ctx.response.defer()

        speaker_name = speaker
        speaker_id = voicevox.get_speaker_id(speaker_name)
        if ctx.user.id in dict_db["user_settings"]:
            dict_db["user_settings"][ctx.user.id]["speaker_name"] = speaker_name
            dict_db["user_settings"][ctx.user.id]["speaker_id"] = speaker_id
        else:
            dict_db["user_settings"][ctx.user.id] = {"speaker_name": speaker_name, "speaker_id": speaker_id}
        await database.update_user_speaker(ctx.user.id, speaker_id, speaker_name)
        await ctx.followup.send(f"音声を {speaker_name}({voicevox.get_speaker_style_name(speaker_id)}) に設定しました。")

    # /set_voice_style
    @tree.command(
        name="set_voice_style",
        description="声色を設定します。"
    )
    @discord.app_commands.autocomplete(
        style=autocomplete_style
    )
    async def set_voice_style(ctx: discord.Interaction, style: str):
        await ctx.response.defer()

        speaker_name = dict_db["user_settings"].get(ctx.user.id, {}).get("speaker_name", "ずんだもん")
        speaker_id = voicevox.get_speaker_id(speaker_name, style) or 3
        if ctx.user.id in dict_db["user_settings"]:
            dict_db["user_settings"][ctx.user.id]["speaker_id"] = speaker_id
        else:
            dict_db["user_settings"][ctx.user.id] = {"speaker_id": speaker_id, "speaker_name": speaker_name}
        await database.update_user_speaker(ctx.user.id, speaker_id, speaker_name)
        await ctx.followup.send(f"声色を {speaker_name}({voicevox.get_speaker_style_name(speaker_id)}) に設定しました。")

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
        await database.update_user_speed(ctx.user.id, speed)
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

                message_content, speaker_id, speak_speed = voice_queues[guild_id].popleft()
                wav_data = await voicevox.get_voice(message_content, speaker_id=speaker_id, speak_speed=speak_speed)

                # asyncio.Eventで再生完了を通知
                play_done = asyncio.Event()

                def after_play(error):
                    if error:
                        print(f"再生エラー: {error}")
                    client.loop.call_soon_threadsafe(play_done.set)

                voice_client.play(
                    discord.FFmpegPCMAudio(io.BytesIO(wav_data), **VoiceBox.ffmpeg_options),
                    after=after_play
                )
                await play_done.wait()
        except Exception as e:
            print(f"キュー処理中にエラーが発生しました: {e}")
        finally:
            processing_queues[guild_id] = False

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        if message.guild is None or message.guild.voice_client is None:
            return

        guild_id = message.guild.id
        server_settings = dict_db["server_settings"].get(guild_id)
        if not server_settings:
            return
        if message.channel.id != server_settings.get("read_channel"):
            return

        try:
            content = preprocess_text(message.content)
            if not content.strip():
                return

            speaker_id = dict_db["user_settings"].get(message.author.id, {}).get("speaker_id", 3)
            speak_speed = dict_db["user_settings"].get(message.author.id, {}).get("speed", 1.0)

            if guild_id not in voice_queues:
                voice_queues[guild_id] = deque()
            voice_queues[guild_id].append((content, speaker_id, speak_speed))
            asyncio.create_task(process_voice_queue(guild_id))
        except Exception as e:
            print(f"メッセージ処理中にエラーが発生しました: {e}")

    @client.event
    async def on_voice_state_update(member, before, after):
        if member.guild.voice_client is None:
            return
        if before.channel != member.guild.voice_client.channel:
            return
        if after.channel == before.channel:
            return
        # ボット以外のメンバーがいなくなったら切断
        if len(member.guild.voice_client.channel.members) == 1:
            await member.guild.voice_client.disconnect()
            read_channel_id = dict_db["server_settings"].get(member.guild.id, {}).get("read_channel")
            if read_channel_id:
                read_channel = member.guild.get_channel(read_channel_id)
                if read_channel:
                    await read_channel.send("全員が退出したため、切断しました。")
                    return
            if member.guild.text_channels:
                await member.guild.text_channels[0].send("全員が退出したため、切断しました。")
