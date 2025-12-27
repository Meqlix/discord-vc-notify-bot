import os
import json
import discord
from discord.ext import commands
from collections import defaultdict

# ===== 保存ファイル =====
CONFIG_FILE = "channels.json"

def load_channels():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_channels(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

guild_channels = load_channels()

# ===== Intents =====
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== 投票 =====
vote_state = defaultdict(set)

CHOICES = [
    "今すぐ(30分以内)",
    "1-3時間後",
    "3時間以上後",
    "今日は無理"
]

def make_embed():
    embed = discord.Embed(
        title="🗳 通話できる？",
        description="押したボタンの所にメンションで表示されるよ",
        color=0x00ffcc
    )
    for choice in CHOICES:
        names = "、".join(vote_state[choice]) if vote_state[choice] else "なし"
        embed.add_field(name=choice, value=names, inline=False)
    return embed


class VoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def register(self, interaction: discord.Interaction, choice: str):
        user = interaction.user.mention
        for v in vote_state.values():
            v.discard(user)
        vote_state[choice].add(user)

        await interaction.response.edit_message(
            embed=make_embed(),
            view=self
        )

    @discord.ui.button(label="① 今すぐ", style=discord.ButtonStyle.green)
    async def now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "今すぐ(30分以内)")

    @discord.ui.button(label="② 1-3時間後", style=discord.ButtonStyle.blurple)
    async def later(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "1-3時間後")

    @discord.ui.button(label="③ 3時間以上後", style=discord.ButtonStyle.gray)
    async def later_more(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "3時間以上後")

    @discord.ui.button(label="④ 今日は無理", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "今日は無理")


# ===== Slash Commands =====
@bot.tree.command(name="setchannel", description="このチャンネルを通話通知用に設定")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def setchannel(interaction: discord.Interaction):
    guild_channels[str(interaction.guild.id)] = interaction.channel.id
    save_channels(guild_channels)
    await interaction.response.send_message(
        "✅ このチャンネルを通話通知用に設定したよ",
        ephemeral=True
    )


@bot.tree.command(name="clearchannel", description="通話通知チャンネル設定を解除")
@discord.app_commands.checks.has_permissions(manage_guild=True)
async def clearchannel(interaction: discord.Interaction):
    guild_channels.pop(str(interaction.guild.id), None)
    save_channels(guild_channels)
    await interaction.response.send_message(
        "🗑 通話通知チャンネル設定を解除したよ",
        ephemeral=True
    )


# ===== 起動 =====
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"ログイン完了: {bot.user}")


# ===== VC検知（1人目だけ） =====
@bot.event
async def on_voice_state_update(member, before, after):
    if (
        before.channel is None
        and after.channel is not None
        and len(after.channel.members) == 1
    ):
        channel_id = guild_channels.get(str(member.guild.id))
        if channel_id is None:
            return

        channel = member.guild.get_channel(channel_id)
        if channel is None:
            return

        vote_state.clear()

        await channel.send(
            content="@everyone 通話始まったよ！参加できる？",
            embed=make_embed(),
            view=VoteView()
        )


bot.run(os.environ["DISCORD_TOKEN"])
