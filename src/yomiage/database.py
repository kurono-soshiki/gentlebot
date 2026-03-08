import aiosqlite
import os
from typing import Optional

DB_PATH = os.environ.get("BOT_DB_PATH", "data/bot.db")


async def init_db():
    """データベースを初期化し、テーブルを作成する"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS server_settings (
                guild_id INTEGER PRIMARY KEY,
                read_channel_id INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                speaker_id INTEGER NOT NULL DEFAULT 3,
                speaker_name TEXT NOT NULL DEFAULT 'ずんだもん',
                speed REAL NOT NULL DEFAULT 1.0
            )
        """)
        await db.commit()


async def get_server_setting(guild_id: int) -> Optional[int]:
    """サーバーの読み上げチャンネルIDを取得する"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT read_channel_id FROM server_settings WHERE guild_id = ?",
            (guild_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_server_setting(guild_id: int, read_channel_id: Optional[int]):
    """サーバーの読み上げチャンネルIDを設定する"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO server_settings (guild_id, read_channel_id)
               VALUES (?, ?)
               ON CONFLICT(guild_id) DO UPDATE SET read_channel_id = ?""",
            (guild_id, read_channel_id, read_channel_id)
        )
        await db.commit()


async def get_user_setting(user_id: int) -> Optional[dict]:
    """ユーザーの音声設定を取得する"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT speaker_id, speaker_name, speed FROM user_settings WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row:
            return {
                "speaker_id": row["speaker_id"],
                "speaker_name": row["speaker_name"],
                "speed": row["speed"]
            }
        return None


async def set_user_setting(user_id: int, speaker_id: int = 3, speaker_name: str = "ずんだもん", speed: float = 1.0):
    """ユーザーの音声設定を保存する"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO user_settings (user_id, speaker_id, speaker_name, speed)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   speaker_id = ?,
                   speaker_name = ?,
                   speed = ?""",
            (user_id, speaker_id, speaker_name, speed, speaker_id, speaker_name, speed)
        )
        await db.commit()


async def update_user_speaker(user_id: int, speaker_id: int, speaker_name: str):
    """ユーザーの話者設定を更新する"""
    current = await get_user_setting(user_id)
    speed = current["speed"] if current else 1.0
    await set_user_setting(user_id, speaker_id, speaker_name, speed)


async def update_user_speed(user_id: int, speed: float):
    """ユーザーの速度設定を更新する"""
    current = await get_user_setting(user_id)
    speaker_id = current["speaker_id"] if current else 3
    speaker_name = current["speaker_name"] if current else "ずんだもん"
    await set_user_setting(user_id, speaker_id, speaker_name, speed)


async def load_all_server_settings() -> dict:
    """全サーバー設定をメモリにロードする"""
    settings = {}
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT guild_id, read_channel_id FROM server_settings")
        rows = await cursor.fetchall()
        for row in rows:
            settings[row[0]] = {"read_channel": row[1]}
    return settings


async def load_all_user_settings() -> dict:
    """全ユーザー設定をメモリにロードする"""
    settings = {}
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id, speaker_id, speaker_name, speed FROM user_settings")
        rows = await cursor.fetchall()
        for row in rows:
            settings[row[0]] = {
                "speaker_id": row[1],
                "speaker_name": row[2],
                "speed": row[3]
            }
    return settings
