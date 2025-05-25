import requests
import discord
import config
import json

class VoiceBox:
    ffmpeg_options = {
        'pipe': True,
    }

    def __init__(self):
        query_url = "http://voicebox:50021/speakers"
        # 200が返るまでリクエストを送り続ける
        # while True:
        #     response = requests.get(query_url)
        #     if response.status_code == 200:
        #         self.speakers_json = response.json()
        #         break
        # response = requests.get(query_url)
        self.speakers_json = self.local_speakers_json()

        speaker_list = []
        for speaker in self.speakers_json:
            for style in speaker["styles"]:
                if style["name"] == "ノーマル":
                    speaker_list.append({
                        "name": speaker["name"],
                        "style": style["name"],
                        "id": style["id"]
                    })
        self.speaker_list = speaker_list
        

    # 文字列を受け取り、voice boxのhttpリクエストに投げてwavを返す
    def get_voice(self, text: str, speaker_id: str = "3", speak_speed: float = 1.0):
        audio_query_url = "http://voicebox:50021/audio_query"
        audio_response = requests.post(
            audio_query_url,
            params={
                "text": text,
                "speaker": speaker_id
            }
        )
        query_json = audio_response.json()

        # 速度を変更
        query_json["speedScale"] = speak_speed

        synthesis_url = "http://voicebox:50021/synthesis"
        synthesis_response = requests.post(
            synthesis_url,
            json=query_json,
            stream=True,
            params={
                "speaker": speaker_id
            }
        )

        return synthesis_response.raw


    def get_speaker_name(self, speaker_name: str):
        speakers = self.speakers_json
        for speaker in speakers:
            if speaker["speaker_name"] == speaker_name:
                return speaker["name"]
        return None
    
    def get_speaker_id(self, speaker_name: str, style_name: str = "ノーマル"):
        speakers = self.speakers_json
        for speaker in speakers:
            for style in speaker["styles"]:
                if speaker["name"] == speaker_name:
                    if style["name"] == style_name:
                        return style["id"]
        return None

    def get_speaker_style_name(self, speaker_id: int):
        speakers = self.speakers_json
        for speaker in speakers:
            for style in speaker["styles"]:
                if style["id"] == speaker_id:
                    return style["name"]
    
    def local_speakers_json(self):
        # ローカルに保存しているjsonを読み込む
        import os
        json_path = os.path.join(os.path.dirname(__file__), 'voice.json')
        json_open = open(json_path, 'r')
        json_load = json.load(json_open)
        return json_load

    def get_speaker_list(self):
        return self.speaker_list


    def get_style_list(self, speaker_name: str):
        speakers = self.speakers_json
        for speaker in speakers:
            if speaker["name"] == speaker_name:
                return speaker["styles"]
        return None
    
    def build_speaker_choices(self):
        choices = []
        for speaker in self.speaker_list:
            choices.append(
                discord.app_commands.Choice(name=speaker["name"], value=speaker["name"])
            )
        return choices