import discord
from discord.ext import commands

from bot import *


class TemplateCog(commands.Cog):
	"""Description"""

	def __init__(self, bot: commands.bot):
		self.bot = bot


	@commands.command()
	async def command(self, ctx):
		"""Description"""
		await p(ctx, "hello world")
