import os
import discord
from discord.ext import commands
from collections import defaultdict

# ===== Intents =====
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== 投票状態 =====
vote_state = defaultdict(set)

CHOICES = [
    "今すぐ(15分以内)",
    "15分-1時間後",
    "1-3時間後",
    "3時間以上後"
]

def make_embed():
    embed = discord.Embed(
        title="📞 通話こい！！",
        description="いつ来れる？",
        color=0x00ffcc
    )

    for choice in CHOICES:
        names = "、".join(vote_state[choice]) if vote_state[choice] else "なし"
        embed.add_field(name=choice, value=names, inline=False)

    return embed


# ===== 投票ボタン =====
class VoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def register(self, interaction: discord.Interaction, choice: str):
        user = interaction.user.mention  # メンション表示

        # 他の選択肢から削除
        for v in vote_state.values():
            v.discard(user)

        vote_state[choice].add(user)

        await interaction.response.edit_message(
            embed=make_embed(),
            view=self
        )

    @discord.ui.button(label="① 今すぐ(15分以内))", style=discord.ButtonStyle.green)
    async def now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "今すぐ(15分以内)")

    @discord.ui.button(label="② 15分-1時間後", style=discord.ButtonStyle.blurple)
    async def later(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "15分-1時間後")

    @discord.ui.button(label="③ 1-3時間後", style=discord.ButtonStyle.gray)
    async def much_later(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "1-3時間後")

    @discord.ui.button(label="④ 3時間以上後", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "3時間以上後")


# ===== 起動確認 =====
@bot.event
async def on_ready():
    print(f"ログイン完了: {bot.user}")


# ===== VC入室検知（1人目だけ） =====
@bot.event
async def on_voice_state_update(member, before, after):
    # VCが空の状態 → 最初の1人が入った時だけ
    if (
        before.channel is None
        and after.channel is not None
        and len(after.channel.members) == 1
    ):
        # 送信できる最初のテキストチャンネルを探す
        channel = None
        for ch in member.guild.text_channels:
            if ch.permissions_for(member.guild.me).send_messages:
                channel = ch
                break

        if channel is None:
            return

        # 投票リセット
        vote_state.clear()

        await channel.send(
            content="@everyone",
            embed=make_embed(),
            view=VoteView()
        )


# ===== 起動 =====
bot.run(os.environ["DISCORD_TOKEN"])
