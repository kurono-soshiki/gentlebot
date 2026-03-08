## 起動方法

```
$ sudo docker compose up -d --build
```

## 開発環境

パッケージ管理には [uv](https://docs.astral.sh/uv/) を使用しています。
また、ローカルのツールチェイン管理には [mise](https://mise.jdx.dev/) を使用できます。

### mise を使う場合

```bash
# mise が使える状態でツールを揃える
$ mise install

# 依存関係のインストール
$ uv sync

# botの起動
$ uv run python src/main.py

# テストの実行
$ uv run python -m pytest
```

`mise.toml` では Docker と合わせて Python 3.12 を使うようにしています。
Docker 側もプロジェクト直下の `.venv` を使わず、コンテナ内の専用仮想環境を使うようにしてあるため、ホスト側の Python バージョン差分に引っ張られにくくなっています。

```bash
# 依存関係のインストール
$ uv sync

# botの起動
$ uv run python src/main.py

# テストの実行
$ uv run python -m pytest
```

## 読み上げ使い方

### 読み上げるチャンネルを登録する

現在のテキストチャンネルを登録する
/set_read_channel

現在のテキストチャンネルの登録を解除する
/unset_read_channel

### VCにbotを参加させる

現在のVCに参加する、/set_read_channelの機能を内包している
/join

VCから退出する、ユーザーがVCから退出した場合も自動で退出する
/leave

### 読み上げる
VCにbotが参加している状態で、登録したテキストチャンネルにメッセージを送信すると読み上げます。


### 読み上げ設定

読み上げの音声を変更する
/set_voice <音声名>

読み上げの音声のスタイルを変更する
/set_voice_style <スタイル名>

読み上げの速度を変更する
/set_speed <速度>
