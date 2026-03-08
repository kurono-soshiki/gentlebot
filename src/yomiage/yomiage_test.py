import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch
from yomiage.yomiage import dict_db, voice_queues, processing_queues, preprocess_text


class TestPreprocessText(unittest.TestCase):
    """preprocess_text関数のテスト"""

    def test_url_replacement(self):
        text = "こんにちは https://example.com/path?query=1 これはテストです"
        result = preprocess_text(text)
        self.assertIn("URL省略", result)
        self.assertNotIn("https://", result)

    def test_newline_to_space(self):
        text = "行1\n行2\n行3"
        result = preprocess_text(text)
        self.assertNotIn("\n", result)
        self.assertIn("行1 行2 行3", result)

    def test_length_limit(self):
        text = "あ" * 150
        result = preprocess_text(text)
        self.assertTrue(result.endswith("以下省略"))
        self.assertLessEqual(len(result), 105)  # 100 + len("以下省略")

    def test_special_chars_removed(self):
        text = "テスト゛゜"
        result = preprocess_text(text)
        self.assertNotIn("゛", result)
        self.assertNotIn("゜", result)

    def test_empty_content(self):
        text = ""
        result = preprocess_text(text)
        self.assertEqual(result, "")


class TestYomiageFunctions(unittest.TestCase):
    def setUp(self):
        dict_db["server_settings"] = {}
        dict_db["user_settings"] = {}
        voice_queues.clear()
        processing_queues.clear()

    def test_dict_db_structure(self):
        """Test the initial structure of the dict_db dictionary"""
        self.assertIn("server_settings", dict_db)
        self.assertIn("user_settings", dict_db)
        self.assertEqual(dict_db["server_settings"], {})
        self.assertEqual(dict_db["user_settings"], {})

    @patch("discord.app_commands.CommandTree")
    @patch("discord.Client")
    def test_setup_registers_commands(self, mock_client, mock_tree):
        """Test that setup registers the expected commands"""
        from yomiage.yomiage import setup

        setup(mock_tree, mock_client)
        self.assertGreaterEqual(mock_tree.command.call_count, 1)


if __name__ == "__main__":
    unittest.main()
