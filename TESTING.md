# テスト・ガイド

このドキュメントはDiscord TTSボットのテストの実行方法と記述方法について説明します。

## テストの実行

### 前提条件

- Python 3.12以降
- Poetry

### すべてのテストの実行

すべてのテストを実行するには、次のコマンドを実行します：

```bash
poetry run python src/test_runner.py
```

### テスト用環境変数

外部サービス（GoogleのGemini APIなど）と連携するテストではAPIキーが必要です。CI環境では、これらはGitHubシークレットとして提供されます。ローカル開発では、`.env`ファイルまたは環境に直接設定できます。

テストに必要な環境変数：
- `DISCORD_TOKEN`: Discordボットトークン
- `GEMINI_API_KEY`: Google Gemini APIキー

これらの環境変数が利用できない場合、それらを必要とするテストは適切なメッセージとともにスキップされます。

## テストの作成

### テストの構成

テストは対応するモジュールと共に構成されています：

- `umigame/umigame_test.py`: うみがめモジュールのテスト
- `yomiage/voicebox_test.py`: ボイスボックスモジュールのテスト
- `yomiage/yomiage_test.py`: 読み上げモジュールのテスト

### テストのパターン

1. **外部依存のモック**
   
   外部サービスやAPIに依存する関数には、`unittest.mock`モジュールを使用してレスポンスをモックします：

   ```python
   @patch('google.genai.Client')
   @patch('config.GEMINI_API_KEY', 'mock_api_key')
   def test_gemini_generate_mock(self, mock_client):
       # テスト実装
   ```

2. **非同期関数のテスト**
   
   非同期関数の場合は、テストループを使用してコルーチンを実行します：

   ```python
   def setUp(self):
       # 各テストごとに新しいイベントループを作成
       self.loop = asyncio.new_event_loop()
       asyncio.set_event_loop(self.loop)

   def tearDown(self):
       # 各テスト後にイベントループを閉じる
       self.loop.close()
       
   def test_async_function(self):
       result = self.loop.run_until_complete(some_async_function())
   ```

3. **テストのスキップ**
   
   テストに特定の環境変数が必要な場合は、条件付きスキップを使用します：

   ```python
   @unittest.skipIf(not getattr(config, 'GEMINI_API_KEY', None), "GEMINI_API_KEYが設定されていません")
   def test_gemini_generate_real_api(self):
       # 実際のAPI呼び出しのためのテスト実装
   ```

## 継続的インテグレーション

このプロジェクトではGitHub ActionsをCIに使用しています。ワークフローは`.github/workflows/tests.yml`で定義されており、メインブランチへのプッシュとプルリクエストで自動的に実行されます。