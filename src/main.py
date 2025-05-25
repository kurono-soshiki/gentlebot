import discord
import config
from yomiage import yomiage as yomiage_bot
from umigame import umigame as umigame_bot

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

yomiage_bot.setup(tree, client)
umigame_bot.setup(tree, client)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    # グローバルコマンドの同期
    await tree.sync()
    print("グローバルスラッシュコマンドを同期しました")
    # ギルドごとのコマンドの同期
    for guild in client.guilds:
        await tree.sync(guild=discord.Object(id=guild.id))
        print(f"スラッシュコマンドをギルド {guild.id} に同期しました")

client.run(config.DISCORD_TOKEN)
