import os
import discord
from discord.ext import commands
from collections import defaultdict

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
        user = interaction.user.mention  # ← ここが重要（青文字）

        # 他の選択肢から削除
        for v in vote_state.values():
            v.discard(user)

        vote_state[choice].add(user)

        await interaction.response.edit_message(
            embed=make_embed(),
            view=self
        )

    @discord.ui.button(label="① 今すぐ(30分以内)", style=discord.ButtonStyle.green)
    async def now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "今すぐ(30分以内)")

    @discord.ui.button(label="② 1-3時間後", style=discord.ButtonStyle.blurple)
    async def later(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "1-3時間後")

    @discord.ui.button(label="③ 3時間以上後", style=discord.ButtonStyle.gray)
    async def much_later(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "3時間以上後")

    @discord.ui.button(label="④ 今日は無理", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "今日は無理")


@bot.event
async def on_ready():
    print(f"ログイン完了: {bot.user}")


@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        channel = None

        for ch in member.guild.text_channels:
            if ch.permissions_for(member.guild.me).send_messages:
                channel = ch
                break

        if channel is None:
            return

        vote_state.clear()

        await channel.send(
            content="@everyone 通話始まったよ！参加できる？",
            embed=make_embed(),
            view=VoteView()
        )


bot.run(os.environ["DISCORD_TOKEN"])
