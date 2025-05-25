import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from umigame import UmigameGame
import config

class TestGeminiGenerate(unittest.TestCase):
    @unittest.skipIf(not getattr(config, 'GEMINI_API_KEY', None), "GEMINI_API_KEY is not set or accessible in config.py. Skipping real API test.")
    def test_gemini_generate_real_api(self):
        prompt = "こんにちは、元気ですか？"
        print("\nRunning test_gemini_generate_real_api...")
        try:
            # staticmethodなのでクラスから呼び出す
            result = UmigameGame.gemini_generate(prompt)
            print(f"Real API call to gemini_generate returned: {str(result)[:200]}...")
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0, "API response should not be empty.")
        except Exception as e:
            self.fail(f"Real API call to gemini_generate failed: {e}")

if __name__ == '__main__':
    unittest.main()
