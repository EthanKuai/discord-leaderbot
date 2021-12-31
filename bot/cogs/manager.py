import discord
from discord.ext import commands

from bot import *


class ManagerCog(commands.Cog):
	"""Regarding manager role given to those to reset the game etc."""

	def __init__(self, bot: commands.bot, db: db_accessor):
		self.bot = bot
		self.db = db


	@commands.command()
	@check_server()
	@check_manager()
	@confirmation()
	async def reset(self, ctx):
		"""resets game"""
		self.db.reset_scoreboard()
		await ctx.reply("Game reset!")


	"""
	send messages to all channels for scoreboard each
	update leaderboards message
	create command to set roles for others (manager)
	reset points for everyone
	"""
