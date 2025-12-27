import discord
from discord import app_commands
from discord.ext import commands
import json
import os

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

CONFIG_FILE = "channels.json"

# -------- 設定読み書き --------
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

config = load_config()

# -------- 起動時 --------
@bot.event
async def on_ready():
    await bot.tree.sync()  # ← これ1回だけ
    print(f"Logged in as {bot.user}")

# -------- /setchannel --------
@bot.tree.command(name="setchannel", description="通話通知を送るチャンネルを設定します")
@app_commands.checks.has_permissions(administrator=True)
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    config[guild_id] = channel.id
    save_config(config)

    await interaction.response.send_message(
        f"✅ 通話通知チャンネルを {channel.mention} に設定したよ",
        ephemeral=True
    )

# -------- 通話検知 --------
@bot.event
async def on_voice_state_update(member, before, after):
    # 通話に「最初の1人」が入った時だけ
    if before.channel is None and after.channel is not None:
        members = after.channel.members
        if len(members) != 1:
            return

        guild_id = str(member.guild.id)
        if guild_id not in config:
            return

        channel = bot.get_channel(config[guild_id])
        if channel is None:
            return

        view = discord.ui.View(timeout=None)
        results = {
            "now": [],
            "soon": [],
            "later": [],
            "no": []
        }

        async def update_message():
            text = (
                "📞 **通話どう？**\n\n"
                f"🟢 今すぐ: {' '.join(u.mention for u in results['now']) or 'なし'}\n"
                f"🟡 1–3時間後: {' '.join(u.mention for u in results['soon']) or 'なし'}\n"
                f"🟠 3時間以上後: {' '.join(u.mention for u in results['later']) or 'なし'}\n"
                f"🔴 今日は無理: {' '.join(u.mention for u in results['no']) or 'なし'}"
            )
            await message.edit(content=text, view=view)

        async def make_button(label, key):
            async def callback(interaction: discord.Interaction):
                for v in results.values():
                    if interaction.user in v:
                        v.remove(interaction.user)
                results[key].append(interaction.user)
                await interaction.response.defer()
                await update_message()

            button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
            button.callback = callback
            return button

        view.add_item(await make_button("今すぐ", "now"))
        view.add_item(await make_button("1-3時間後", "soon"))
        view.add_item(await make_button("3時間以上後", "later"))
        view.add_item(await make_button("今日は無理", "no"))

        message = await channel.send(
            f"📞 **通話始まったよ！** {member.mention}",
            view=view
        )

# -------- 起動 --------
bot.run(os.environ["DISCORD_TOKEN"])
