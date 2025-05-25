import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from yomiage.voicebox import VoiceBox

class TestVoiceBox(unittest.TestCase):
    @patch('requests.get')
    def test_init_with_request(self, mock_get):
        # This test is commented out since current implementation uses local file
        pass
        # # Mock the response for the speakers query
        # mock_response = MagicMock()
        # mock_response.status_code = 200
        # mock_response.json.return_value = [
        #     {
        #         "name": "テスト話者1",
        #         "styles": [
        #             {"name": "ノーマル", "id": "1"}
        #         ]
        #     },
        #     {
        #         "name": "テスト話者2",
        #         "styles": [
        #             {"name": "ノーマル", "id": "2"},
        #             {"name": "怒り", "id": "3"}
        #         ]
        #     }
        # ]
        # mock_get.return_value = mock_response
        
        # # Initialize the VoiceBox
        # voice_box = VoiceBox()
        
        # # Assertions
        # mock_get.assert_called_once_with("http://voicebox:50021/speakers")
        # self.assertEqual(len(voice_box.speaker_list), 2)

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_init_with_local_file(self, mock_json_load, mock_file_open):
        # Mock the JSON data
        mock_json_data = [
            {
                "name": "テスト話者1",
                "styles": [
                    {"name": "ノーマル", "id": "1"}
                ]
            },
            {
                "name": "テスト話者2",
                "styles": [
                    {"name": "ノーマル", "id": "2"},
                    {"name": "怒り", "id": "3"}
                ]
            }
        ]
        mock_json_load.return_value = mock_json_data
        
        # Initialize the VoiceBox
        voice_box = VoiceBox()
        
        # Assertions
        self.assertEqual(len(voice_box.speaker_list), 2)
        self.assertEqual(voice_box.speaker_list[0]["name"], "テスト話者1")
        self.assertEqual(voice_box.speaker_list[0]["id"], "1")
        self.assertEqual(voice_box.speaker_list[1]["name"], "テスト話者2")
        self.assertEqual(voice_box.speaker_list[1]["id"], "2")

    @patch('requests.post')
    def test_get_voice(self, mock_post):
        # Mock responses for the audio_query and synthesis requests
        mock_audio_response = MagicMock()
        mock_audio_response.json.return_value = {"key": "value"}
        
        mock_synthesis_response = MagicMock()
        mock_synthesis_response.raw = b'audio_data'
        
        mock_post.side_effect = [mock_audio_response, mock_synthesis_response]
        
        # Mock local_speakers_json to avoid reading the actual file
        with patch.object(VoiceBox, 'local_speakers_json') as mock_local_speakers:
            mock_local_speakers.return_value = [
                {
                    "name": "テスト話者",
                    "styles": [
                        {"name": "ノーマル", "id": "1"}
                    ]
                }
            ]
            
            # Initialize the VoiceBox and call get_voice
            voice_box = VoiceBox()
            result = voice_box.get_voice("テストテキスト", "1", 1.0)
            
            # Assertions
            self.assertEqual(mock_post.call_count, 2)
            # First call should be to audio_query
            self.assertEqual(mock_post.call_args_list[0][0][0], "http://voicebox:50021/audio_query")
            # Second call should be to synthesis
            self.assertEqual(mock_post.call_args_list[1][0][0], "http://voicebox:50021/synthesis")
            # Check that the returned raw audio is correct
            self.assertEqual(result, b'audio_data')

    def test_get_speaker_id(self):
        # Mock local_speakers_json to avoid reading the actual file
        with patch.object(VoiceBox, 'local_speakers_json') as mock_local_speakers:
            mock_local_speakers.return_value = [
                {
                    "name": "テスト話者1",
                    "styles": [
                        {"name": "ノーマル", "id": "1"},
                        {"name": "怒り", "id": "2"}
                    ]
                },
                {
                    "name": "テスト話者2",
                    "styles": [
                        {"name": "ノーマル", "id": "3"}
                    ]
                }
            ]
            
            # Initialize the VoiceBox
            voice_box = VoiceBox()
            
            # Test getting speaker IDs
            self.assertEqual(voice_box.get_speaker_id("テスト話者1"), "1")  # Default style is ノーマル
            self.assertEqual(voice_box.get_speaker_id("テスト話者1", "怒り"), "2")
            self.assertEqual(voice_box.get_speaker_id("テスト話者2"), "3")
            self.assertIsNone(voice_box.get_speaker_id("存在しない話者"))
            self.assertIsNone(voice_box.get_speaker_id("テスト話者1", "存在しないスタイル"))

    def test_get_speaker_style_name(self):
        # Mock local_speakers_json to avoid reading the actual file
        with patch.object(VoiceBox, 'local_speakers_json') as mock_local_speakers:
            mock_local_speakers.return_value = [
                {
                    "name": "テスト話者1",
                    "styles": [
                        {"name": "ノーマル", "id": 1},
                        {"name": "怒り", "id": 2}
                    ]
                }
            ]
            
            # Initialize the VoiceBox
            voice_box = VoiceBox()
            
            # Test getting style names
            self.assertEqual(voice_box.get_speaker_style_name(1), "ノーマル")
            self.assertEqual(voice_box.get_speaker_style_name(2), "怒り")
            self.assertIsNone(voice_box.get_speaker_style_name(999))  # Non-existent ID

if __name__ == '__main__':
    unittest.main()