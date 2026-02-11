import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import asyncio
import tempfile
from yomiage import database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # テスト用の一時DBファイルを使用
        self.tmp_dir = tempfile.mkdtemp()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = os.path.join(self.tmp_dir, "test.db")
        self.loop.run_until_complete(database.init_db())

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        self.loop.close()
        # 一時ファイルを削除
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_init_db_creates_tables(self):
        """init_dbでテーブルが作成されることを確認"""
        # init_dbはsetUpで呼ばれている
        # 2回呼んでもエラーにならないことを確認
        self.loop.run_until_complete(database.init_db())

    def test_server_settings(self):
        """サーバー設定のCRUDテスト"""
        guild_id = 123456789

        # 初期状態ではNone
        result = self.loop.run_until_complete(database.get_server_setting(guild_id))
        self.assertIsNone(result)

        # 設定を保存
        self.loop.run_until_complete(database.set_server_setting(guild_id, 987654321))
        result = self.loop.run_until_complete(database.get_server_setting(guild_id))
        self.assertEqual(result, 987654321)

        # 設定を更新
        self.loop.run_until_complete(database.set_server_setting(guild_id, 111111111))
        result = self.loop.run_until_complete(database.get_server_setting(guild_id))
        self.assertEqual(result, 111111111)

        # Noneに設定
        self.loop.run_until_complete(database.set_server_setting(guild_id, None))
        result = self.loop.run_until_complete(database.get_server_setting(guild_id))
        self.assertIsNone(result)

    def test_user_settings(self):
        """ユーザー設定のCRUDテスト"""
        user_id = 111222333

        # 初期状態ではNone
        result = self.loop.run_until_complete(database.get_user_setting(user_id))
        self.assertIsNone(result)

        # 設定を保存
        self.loop.run_until_complete(
            database.set_user_setting(user_id, speaker_id=5, speaker_name="四国めたん", speed=1.5)
        )
        result = self.loop.run_until_complete(database.get_user_setting(user_id))
        self.assertIsNotNone(result)
        self.assertEqual(result["speaker_id"], 5)
        self.assertEqual(result["speaker_name"], "四国めたん")
        self.assertEqual(result["speed"], 1.5)

    def test_update_user_speaker(self):
        """ユーザーの話者設定更新テスト"""
        user_id = 444555666

        # まず初期設定を保存
        self.loop.run_until_complete(
            database.set_user_setting(user_id, speaker_id=3, speaker_name="ずんだもん", speed=2.0)
        )

        # 話者のみ変更（speedは維持される）
        self.loop.run_until_complete(
            database.update_user_speaker(user_id, speaker_id=5, speaker_name="四国めたん")
        )
        result = self.loop.run_until_complete(database.get_user_setting(user_id))
        self.assertEqual(result["speaker_id"], 5)
        self.assertEqual(result["speaker_name"], "四国めたん")
        self.assertEqual(result["speed"], 2.0)  # 速度は変わらない

    def test_update_user_speed(self):
        """ユーザーの速度設定更新テスト"""
        user_id = 777888999

        # まず初期設定を保存
        self.loop.run_until_complete(
            database.set_user_setting(user_id, speaker_id=5, speaker_name="四国めたん", speed=1.0)
        )

        # 速度のみ変更（話者は維持される）
        self.loop.run_until_complete(database.update_user_speed(user_id, speed=2.5))
        result = self.loop.run_until_complete(database.get_user_setting(user_id))
        self.assertEqual(result["speaker_id"], 5)  # 話者は変わらない
        self.assertEqual(result["speaker_name"], "四国めたん")
        self.assertEqual(result["speed"], 2.5)

    def test_load_all_server_settings(self):
        """全サーバー設定のロードテスト"""
        # 複数サーバーの設定を保存
        self.loop.run_until_complete(database.set_server_setting(100, 200))
        self.loop.run_until_complete(database.set_server_setting(300, 400))

        result = self.loop.run_until_complete(database.load_all_server_settings())
        self.assertEqual(len(result), 2)
        self.assertEqual(result[100]["read_channel"], 200)
        self.assertEqual(result[300]["read_channel"], 400)

    def test_load_all_user_settings(self):
        """全ユーザー設定のロードテスト"""
        self.loop.run_until_complete(
            database.set_user_setting(10, speaker_id=3, speaker_name="ずんだもん", speed=1.0)
        )
        self.loop.run_until_complete(
            database.set_user_setting(20, speaker_id=5, speaker_name="四国めたん", speed=1.5)
        )

        result = self.loop.run_until_complete(database.load_all_user_settings())
        self.assertEqual(len(result), 2)
        self.assertEqual(result[10]["speaker_id"], 3)
        self.assertEqual(result[20]["speaker_name"], "四国めたん")

    def test_update_user_speaker_no_existing(self):
        """既存設定がない場合のupdate_user_speakerテスト"""
        user_id = 999000111
        self.loop.run_until_complete(
            database.update_user_speaker(user_id, speaker_id=5, speaker_name="四国めたん")
        )
        result = self.loop.run_until_complete(database.get_user_setting(user_id))
        self.assertEqual(result["speaker_id"], 5)
        self.assertEqual(result["speed"], 1.0)  # デフォルト値

    def test_update_user_speed_no_existing(self):
        """既存設定がない場合のupdate_user_speedテスト"""
        user_id = 222333444
        self.loop.run_until_complete(database.update_user_speed(user_id, speed=2.0))
        result = self.loop.run_until_complete(database.get_user_setting(user_id))
        self.assertEqual(result["speaker_id"], 3)  # デフォルト値
        self.assertEqual(result["speaker_name"], "ずんだもん")  # デフォルト値
        self.assertEqual(result["speed"], 2.0)


if __name__ == '__main__':
    unittest.main()
