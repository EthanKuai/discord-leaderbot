import discord
from discord.ext import commands
from discord.utils import get

from bot import *


class RoleCog(commands.Cog):
	"""Creates & allows users to add specific roles."""

	def __init__(self, bot: commands.bot, db: db_accessor):
		self.bot = bot
		self.db = db


	@commands.command()
	async def command(self, ctx):
		"""Description"""
		member = ctx.message.author
		role = get(member.server.roles, name="Test")
		await self.bot.add_roles(member, role)

"""
async def giverole(ctx, user: discord.Member, role: discord.Role):
    await user.add_roles(role)
    await ctx.send(f"hey {ctx.author.name}, {user.name} has been giving a role called: {role.name}")
"""
