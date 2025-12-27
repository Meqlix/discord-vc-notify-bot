import discord
from discord.ext import commands

import os
TOKEN = os.getenv("DISCORD_TOKEN")

NOTICE_CHANNEL_ID = 1066819936867065960  # お知らせを出したいチャンネルID

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

class JoinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="今すぐ（30分以内）", style=discord.ButtonStyle.success)
    async def now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🟢 今すぐ参加できる！", ephemeral=True)

    @discord.ui.button(label="1〜3時間後", style=discord.ButtonStyle.primary)
    async def later(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🟡 1〜3時間後ならOK！", ephemeral=True)

    @discord.ui.button(label="3時間以上後", style=discord.ButtonStyle.secondary)
    async def much_later(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔵 3時間以上後ならOK！", ephemeral=True)

    @discord.ui.button(label="今日は無理", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔴 今日は無理！", ephemeral=True)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        channel = bot.get_channel(NOTICE_CHANNEL_ID)
        if channel:
            await channel.send(
                f"@everyone\n**{member.display_name}** が通話に入ったよ\n今からどう？",
                view=JoinView()
            )

bot.run(TOKEN)