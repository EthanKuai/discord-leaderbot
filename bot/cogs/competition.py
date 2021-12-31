import discord
from discord.ext import commands

from bot import *


class CompetitionCog(commands.Cog):
	"""For competitions. Check competition-details.json"""

	def __init__(self, bot: commands.bot, db: db_accessor):
		self.bot = bot
		self.db = db


	@commands.command()
	async def command(self, ctx):
		"""Description"""
		await p(ctx, "hello world")
