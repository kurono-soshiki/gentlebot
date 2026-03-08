import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from yomiage.voicebox import VoiceBox


class TestVoiceBox(unittest.TestCase):
    def _make_voicebox(self, mock_data=None):
        """ヘルパー: モックデータでVoiceBoxを初期化"""
        if mock_data is None:
            mock_data = [
                {"name": "テスト話者1", "styles": [{"name": "ノーマル", "id": "1"}]},
                {"name": "テスト話者2", "styles": [{"name": "ノーマル", "id": "2"}, {"name": "怒り", "id": "3"}]},
            ]
        with patch.object(VoiceBox, "_load_local_speakers", return_value=mock_data):
            return VoiceBox()

    def test_init_with_local_file(self):
        voice_box = self._make_voicebox()
        self.assertEqual(len(voice_box.speaker_list), 2)
        self.assertEqual(voice_box.speaker_list[0]["name"], "テスト話者1")
        self.assertEqual(voice_box.speaker_list[0]["id"], "1")
        self.assertEqual(voice_box.speaker_list[1]["name"], "テスト話者2")
        self.assertEqual(voice_box.speaker_list[1]["id"], "2")

    def test_get_voice(self):
        voice_box = self._make_voicebox([{"name": "テスト話者", "styles": [{"name": "ノーマル", "id": "1"}]}])

        # aiohttp.ClientSessionのモック
        mock_session = AsyncMock()
        mock_audio_resp = AsyncMock()
        mock_audio_resp.json = AsyncMock(return_value={"key": "value"})
        mock_synth_resp = AsyncMock()
        mock_synth_resp.read = AsyncMock(return_value=b"audio_data")

        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        # post のコンテキストマネージャーのモック
        mock_audio_cm = AsyncMock()
        mock_audio_cm.__aenter__ = AsyncMock(return_value=mock_audio_resp)
        mock_audio_cm.__aexit__ = AsyncMock(return_value=False)

        mock_synth_cm = AsyncMock()
        mock_synth_cm.__aenter__ = AsyncMock(return_value=mock_synth_resp)
        mock_synth_cm.__aexit__ = AsyncMock(return_value=False)

        mock_session.post = MagicMock(side_effect=[mock_audio_cm, mock_synth_cm])

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = asyncio.run(voice_box.get_voice("テストテキスト", "1", 1.0))

        self.assertEqual(result, b"audio_data")
        self.assertEqual(mock_session.post.call_count, 2)

    def test_get_speaker_id(self):
        voice_box = self._make_voicebox(
            [
                {"name": "テスト話者1", "styles": [{"name": "ノーマル", "id": "1"}, {"name": "怒り", "id": "2"}]},
                {"name": "テスト話者2", "styles": [{"name": "ノーマル", "id": "3"}]},
            ]
        )

        self.assertEqual(voice_box.get_speaker_id("テスト話者1"), "1")
        self.assertEqual(voice_box.get_speaker_id("テスト話者1", "怒り"), "2")
        self.assertEqual(voice_box.get_speaker_id("テスト話者2"), "3")
        self.assertIsNone(voice_box.get_speaker_id("存在しない話者"))
        self.assertIsNone(voice_box.get_speaker_id("テスト話者1", "存在しないスタイル"))

    def test_get_speaker_style_name(self):
        voice_box = self._make_voicebox(
            [{"name": "テスト話者1", "styles": [{"name": "ノーマル", "id": 1}, {"name": "怒り", "id": 2}]}]
        )

        self.assertEqual(voice_box.get_speaker_style_name(1), "ノーマル")
        self.assertEqual(voice_box.get_speaker_style_name(2), "怒り")
        self.assertIsNone(voice_box.get_speaker_style_name(999))


if __name__ == "__main__":
    unittest.main()
