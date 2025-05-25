from dataclasses import dataclass
import os
import discord
import google.genai as genai
import config
from typing import Tuple


@dataclass
class UmigameProblem:
    problem: str
    reason: str

umigame_sessions = {}

class UmigameGame:
    def __init__(self):
        self.problem = ""
        self.reason = ""
        self.hints = ["" for _ in range(5)]

    @staticmethod
    async def gemini_generate(prompt: str, model_name) -> str:
        os.environ["GOOGLE_API_KEY"] = config.GEMINI_API_KEY
        client = genai.Client()
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"生成に失敗しました（{e}）"
        


    async def generate_problem(self, odai: str = "指定しない") -> str:
        pronpt1 = "新規で作成された良質なうみがめのスープの問題を1つ出題する。答えが突拍子がないものではなく腑に落ちるような内容する。"
        pronpt2 = "あなたはうみがめのスープの出題者。知られていない史実のうんちくを題材として、お～となるような良質なうみがめのスープの問題を1つ出題して。"
        prompt = (
            f"{pronpt1}"
            f"お題は「{odai}」"
            "問題文は長くならないように。回答の足がかりのヒントも作成して、ヒントは数字が大きくなるについれて確信に近づいてほしい、返事は下記のフォーマットに従って。" \
            "<problem>問題文</problem>\n"\
            "<reason>理由文</reason>\n"\
            "<hint1>ヒント1</hint1>\n"\
            "<hint2>ヒント2</hint2>\n"\
            "<hint3>ヒント3</hint3>\n"\
            "<hint4>ヒント4</hint4>\n"\
            "<hint5>ヒント5</hint5>\n"\
        )
        model_name = "gemini-2.5-pro-exp-03-25"

        mondai = await self.gemini_generate(prompt, model_name)
        # 問題文と理由文を分割
        import re
        # <problem>...</problem> と <reason>...</reason> タグ形式で抽出
        match = re.search(r"<problem>(.*?)</problem>.*?<reason>(.*?)</reason>", mondai, re.DOTALL | re.IGNORECASE)

        # <hint1>...</hint1> タグ形式で抽出
        for i in range(1, 6):
            hint_match = re.search(rf"<hint{i}>(.*?)</hint{i}>", mondai, re.DOTALL | re.IGNORECASE)
            if hint_match:
                self.hints[i-1] = hint_match.group(1).strip()
            else:
                self.hints[i-1] = ""

        if match:
            self.problem = match.group(1).strip()
            self.reason = match.group(2).strip()
        else:
            self.problem = mondai.strip()
            self.reason = "理由文の抽出に失敗しました。"

        if not self.problem or not self.reason or self.reason == "理由文の抽出に失敗しました。":
            raise ValueError(f"問題文または理由文が正しく取得できませんでした。{mondai}")
        
        return self.problem

    async def answer_question(self, question: str) -> Tuple[bool, str]:
        """
        理由と質問を受け取り、はい、いいえ、わからないのいずれかの答えを生成する
        正解だった場合はTrueを返す
        """
        correct = False
        prompt = f"""
                あなたはうみがめのスープの出題者。質問と解説を照らし合わせて「正解」「はい」「おおむねはい」「おおむねいいえ」「いいえ」「わからない」のいずれかに判定する。返事は必ず1単語で返す。\n \
                問題: {self.problem}
                問題の解説: {self.reason}
                質問: {question}
                """
        model_name="gemini-2.5-flash-preview-04-17"

        answer = await self.gemini_generate(prompt, model_name)
        # 正解の判定
        if "正解" in answer:
            correct = True
            answer = "正解"
        elif "おおむねはい" in answer:
            answer = "おおむねはい"
        elif "おおむねいいえ" in answer:
            answer = "おおむねいいえ"
        elif "はい" in answer:
            answer = "はい"
        elif "いいえ" in answer:
            answer = "いいえ"
        elif "わからない" in answer:
            answer = "わからない"
        else:
            # それ以外の返答は失敗しましたにする
            answer = "失敗しました。もう一度質問してください。"

        return_answer = [correct, answer]
        return return_answer



def setup(tree: discord.app_commands.CommandTree, client: discord.Client):

    @tree.command(
        name="umigame_start",
        description="うみがめのスープの新しい問題を出題します。"
    )
    async def umigame_start(ctx: discord.Interaction, odai: str = ""):
        guild_id = ctx.guild.id
        await ctx.response.send_message(f"{odai}のうみがめのスープを出題します。しばらくお待ち下さい")
        
        game = UmigameGame()

        # 問題を生成する
        try:
            question = await game.generate_problem(odai)
        except Exception as e:
            await ctx.channel.send(f"問題生成に失敗しました: {e}")
            return

        # 問題を生成したらセッションに保存
        umigame_sessions[guild_id] = game

        await ctx.channel.send(f"【うみがめのスープ】\n{question}")


    @tree.command(
        name="umigame_ask",
        description="うみがめのスープの問題に質問します。"
    )
    @discord.app_commands.describe(question="質問内容（例: 男はうみがめのスープを食べたことがある？）")
    async def umigame_ask(ctx: discord.Interaction, question: str):
        guild_id = ctx.guild.id
        await ctx.response.send_message(f"質問: {question}")

        if guild_id not in umigame_sessions:
            await ctx.channel.send("まず /umigame_start で問題を出題してください。")
            return
        
        game = umigame_sessions[guild_id]
        answer = await game.answer_question(question)
        if answer[0]:
            await ctx.channel.send("正解です！")
            #　正解をしたら解説を送信
            await ctx.channel.send(f"【問題】{game.problem}\n【理由】{game.reason}")
            # セッションを削除
            del umigame_sessions[guild_id]
            return
        else:
            # 正解でない場合はそのまま返す
            await ctx.channel.send(f"質問: {question}\n答え: {answer[1]}")

        
    #問題を確認する
    @tree.command(
        name="umigame_show",
        description="現在のうみがめのスープの問題と答えを表示します（管理用）"
    )
    async def umigame_show(ctx: discord.Interaction):
        guild_id = ctx.guild.id
        if guild_id not in umigame_sessions or not umigame_sessions[guild_id].problem:
            await ctx.response.send_message("現在出題中の問題はありません。")
            return
        game = umigame_sessions[guild_id]
        await ctx.response.send_message(f"【問題】{game.problem}\n【理由】{game.reason}", ephemeral=True)

    #問題をリセットする
    @tree.command(
        name="umigame_reset",
        description="現在のうみがめのスープの問題をリセットします（管理用）"
    )
    async def umigame_reset(ctx: discord.Interaction):
        guild_id = ctx.guild.id
        if guild_id not in umigame_sessions or not umigame_sessions[guild_id].problem:
            await ctx.response.send_message("現在出題中の問題はありません。")
            return
        game = umigame_sessions[guild_id]
        del umigame_sessions[guild_id]
        await ctx.response.send_message(f"問題をリセットしました。\n【問題】{game.problem}\n【理由】{game.reason}")

    #現在の問題文を確認する
    @tree.command(
        name="umigame_current",
        description="現在のうみがめのスープの問題を表示します"
    )
    async def umigame_current(ctx: discord.Interaction):
        guild_id = ctx.guild.id
        if guild_id not in umigame_sessions or not umigame_sessions[guild_id].problem:
            await ctx.response.send_message("現在出題中の問題はありません。")
            return
        game = umigame_sessions[guild_id]
        await ctx.response.send_message(f"【問題】{game.problem}")

    #ヒント1~5を指定して表示する
    @tree.command(
        name="umigame_hint",
        description="うみがめのスープのヒントを表示します"
    )
    @discord.app_commands.describe(hint_number="ヒントの番号（1~5）")
    async def umigame_hint(ctx: discord.Interaction, hint_number: int):
        guild_id = ctx.guild.id
        if guild_id not in umigame_sessions or not umigame_sessions[guild_id].problem:
            await ctx.response.send_message("現在出題中の問題はありません。")
            return
        game = umigame_sessions[guild_id]
        if hint_number < 1 or hint_number > 5:
            await ctx.response.send_message("ヒントの番号は1~5の範囲で指定してください。")
            return
        hint = game.hints[hint_number-1]
        await ctx.response.send_message(f"【ヒント{hint_number}】{hint}")