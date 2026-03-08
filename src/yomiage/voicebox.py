import aiohttp
import discord
import json
import os


class VoiceBox:
    ffmpeg_options = {
        'pipe': True,
    }

    def __init__(self):
        self.speakers_json = self._load_local_speakers()
        self.speaker_list = self._build_speaker_list()

    def _load_local_speakers(self) -> list:
        json_path = os.path.join(os.path.dirname(__file__), 'voice.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_speaker_list(self) -> list:
        speaker_list = []
        for speaker in self.speakers_json:
            for style in speaker["styles"]:
                if style["name"] == "ノーマル":
                    speaker_list.append({
                        "name": speaker["name"],
                        "style": style["name"],
                        "id": style["id"]
                    })
        return speaker_list

    async def get_voice(self, text: str, speaker_id: str = "3", speak_speed: float = 1.0) -> bytes:
        """VOICEVOXにリクエストを送り、音声データを取得する"""
        base_url = "http://voicebox:50021"

        async with aiohttp.ClientSession() as session:
            # audio_queryを取得
            async with session.post(
                f"{base_url}/audio_query",
                params={"text": text, "speaker": speaker_id}
            ) as resp:
                query_json = await resp.json()

            # 速度を変更
            query_json["speedScale"] = speak_speed

            # 音声合成
            async with session.post(
                f"{base_url}/synthesis",
                json=query_json,
                params={"speaker": speaker_id}
            ) as resp:
                return await resp.read()

    def get_speaker_id(self, speaker_name: str, style_name: str = "ノーマル"):
        for speaker in self.speakers_json:
            if speaker["name"] == speaker_name:
                for style in speaker["styles"]:
                    if style["name"] == style_name:
                        return style["id"]
        return None

    def get_speaker_style_name(self, speaker_id: int):
        for speaker in self.speakers_json:
            for style in speaker["styles"]:
                if style["id"] == speaker_id:
                    return style["name"]
        return None

    def get_style_list(self, speaker_name: str):
        for speaker in self.speakers_json:
            if speaker["name"] == speaker_name:
                return speaker["styles"]
        return None

    def build_speaker_choices(self):
        return [
            discord.app_commands.Choice(name=s["name"], value=s["name"])
            for s in self.speaker_list
        ]
