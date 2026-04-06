import discord
import os
from dotenv import load_dotenv
from db.database import init_db, get_blacklist, log_violation

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)


def check_message(content: str) -> list[str]:
    """訊息轉小寫後比對黑名單，回傳所有命中的詞"""
    content_lower = content.lower()
    blacklist = get_blacklist()
    return [word for word in blacklist if word in content_lower]


@client.event
async def on_ready():
    init_db()
    print(f"[Bot] 已登入：{client.user}")
    print(f"[Bot] 已載入黑名單：{len(get_blacklist())} 個詞")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    matched = check_message(message.content)
    if not matched:
        return

    # 記錄違規
    log_violation(
        guild_id=str(message.guild.id),
        channel_id=str(message.channel.id),
        user_id=str(message.author.id),
        username=str(message.author),
        content=message.content,
        matched_words=matched,
    )

    print(f"[違規] {message.author} | 命中：{matched} | 內容：{message.content[:50]}")

    # 傳送警報到 Log 頻道
    if LOG_CHANNEL_ID:
        log_channel = client.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="⚠️ 疑似違規訊息",
                color=discord.Color.red()
            )
            embed.add_field(name="使用者", value=str(message.author), inline=True)
            embed.add_field(name="頻道", value=message.channel.mention, inline=True)
            embed.add_field(name="命中詞彙", value=", ".join(matched), inline=False)
            embed.add_field(name="訊息內容", value=message.content[:500], inline=False)
            embed.set_footer(text=f"User ID: {message.author.id}")
            await log_channel.send(embed=embed)


if __name__ == "__main__":
    client.run(TOKEN)
