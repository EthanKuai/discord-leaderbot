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
	async def startgame(self, ctx):
		"""Starts game"""
		global GAME_ONGOING
		if not GAME_ONGOING:
			GAME_ONGOING = True
			await ctx.reply("Game started!")
		else:
			await ctx.reply("Game already started!")
		# send messages to all channels for evrything

	"""
	create command to set roles for others (manager)
	reset points for everyone
	"""


	@commands.command()
	@check_server()
	@check_manager()
	@check_game()
	async def endgame(self, ctx):
		"""Ends game"""
		global GAME_ONGOING
		GAME_ONGOING = False
		await ctx.reply("Game ended!")
