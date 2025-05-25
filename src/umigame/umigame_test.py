import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from umigame.umigame import UmigameGame
import config

class TestGeminiGenerate(unittest.TestCase):
    @unittest.skipIf(not getattr(config, 'GEMINI_API_KEY', None), "GEMINI_API_KEY is not set or accessible in config.py. Skipping real API test.")
    def test_gemini_generate_real_api(self):
        prompt = "こんにちは、元気ですか？"
        print("\nRunning test_gemini_generate_real_api...")
        try:
            # staticmethodなのでクラスから呼び出す
            result = asyncio.run(UmigameGame.gemini_generate(prompt, "gemini-model"))
            print(f"Real API call to gemini_generate returned: {str(result)[:200]}...")
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0, "API response should not be empty.")
        except Exception as e:
            self.fail(f"Real API call to gemini_generate failed: {e}")

    @patch('google.genai.Client')
    @patch('config.GEMINI_API_KEY', 'mock_api_key')
    def test_gemini_generate_mock(self, mock_client):
        # Mock setup
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_aio = MagicMock()
        mock_client_instance.aio = mock_aio
        mock_models = MagicMock()
        mock_aio.models = mock_models
        mock_generate = AsyncMock()
        mock_models.generate_content = mock_generate
        mock_response = MagicMock()
        mock_response.text = "モックのレスポンスです"
        mock_generate.return_value = mock_response

        # Test execution
        prompt = "テスト用のプロンプト"
        model_name = "test-model"
        result = asyncio.run(UmigameGame.gemini_generate(prompt, model_name))

        # Assertions
        mock_generate.assert_called_once_with(model=model_name, contents=prompt)
        self.assertEqual(result, "モックのレスポンスです")

class TestUmigameGame(unittest.TestCase):
    def setUp(self):
        # Create a new event loop for each test
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        # Close the event loop after each test
        self.loop.close()

    @patch.object(UmigameGame, 'gemini_generate')
    @patch('config.GEMINI_API_KEY', 'mock_api_key')
    def test_generate_problem_parsing(self, mock_generate):
        # Setup mock for gemini_generate
        mock_response = (
            "<problem>テスト問題文</problem>\n"
            "<reason>テスト理由文</reason>\n"
            "<hint1>テストヒント1</hint1>\n"
            "<hint2>テストヒント2</hint2>\n"
            "<hint3>テストヒント3</hint3>\n"
        )
        # Use AsyncMock for the gemini_generate method
        mock_generate.return_value = mock_response

        # Create instance and call method
        game = UmigameGame()
        result = self.loop.run_until_complete(game.generate_problem("テストお題"))

        # Assertions
        self.assertEqual(result, "テスト問題文")
        self.assertEqual(game.problem, "テスト問題文")
        self.assertEqual(game.reason, "テスト理由文")
        self.assertEqual(game.hints[0], "テストヒント1")
        self.assertEqual(game.hints[1], "テストヒント2")
        self.assertEqual(game.hints[2], "テストヒント3")
        self.assertEqual(game.hints[3], "")
        self.assertEqual(game.hints[4], "")

    @patch.object(UmigameGame, 'gemini_generate')
    @patch('config.GEMINI_API_KEY', 'mock_api_key')
    def test_answer_question(self, mock_generate):
        # Create instance and setup
        game = UmigameGame()
        game.problem = "テスト問題"
        game.reason = "テスト理由"
        
        # Test "正解" response
        mock_generate.return_value = "正解です。"
        result = self.loop.run_until_complete(game.answer_question("テスト質問"))
        self.assertTrue(result[0])  # Is correct
        self.assertEqual(result[1], "正解")
        
        # Test "おおむねはい" response - explicitly check that this is processed correctly
        mock_generate.return_value = "おおむねはい"
        result = self.loop.run_until_complete(game.answer_question("テスト質問"))
        self.assertFalse(result[0])  # Not correct
        self.assertEqual(result[1], "おおむねはい")
        
        # Test "おおむねいいえ" response
        mock_generate.return_value = "おおむねいいえ"
        result = self.loop.run_until_complete(game.answer_question("テスト質問"))
        self.assertFalse(result[0])  # Not correct
        self.assertEqual(result[1], "おおむねいいえ")
        
        # Test "はい" response
        mock_generate.return_value = "はい"
        result = self.loop.run_until_complete(game.answer_question("テスト質問"))
        self.assertFalse(result[0])  # Not correct
        self.assertEqual(result[1], "はい")
        
        # Test "いいえ" response
        mock_generate.return_value = "いいえ"
        result = self.loop.run_until_complete(game.answer_question("テスト質問"))
        self.assertFalse(result[0])  # Not correct
        self.assertEqual(result[1], "いいえ")
        
        # Test "わからない" response
        mock_generate.return_value = "わからない"
        result = self.loop.run_until_complete(game.answer_question("テスト質問"))
        self.assertFalse(result[0])  # Not correct
        self.assertEqual(result[1], "わからない")
        
        # Test unexpected response
        mock_generate.return_value = "予期せぬ回答です。"
        result = self.loop.run_until_complete(game.answer_question("テスト質問"))
        self.assertFalse(result[0])  # Not correct
        self.assertEqual(result[1], "失敗しました。もう一度質問してください。")

if __name__ == '__main__':
    unittest.main()
