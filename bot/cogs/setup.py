import discord
from discord.ext import commands

from bot import *


class SetupCog(commands.Cog):
	"""In charge of setting up the server"""

	def __init__(self, bot: commands.bot, db: db_accessor):
		self.bot = bot
		self.db = db


	@commands.command()
	@commands.has_permissions(administrator = True)
	async def setup(self, ctx):
		"""Setup the full server for game, only usable by an admin. First give the bot admin perms."""
		msg = ctx.reply("Would you like to begin the set-up process? Please do NOT stop halfway through.")
		userid = ctx.message.author.id
		# await ctx.guild.create_text_channel(channel_name)

	"""
	save guildid
	create channel for roles
	send save messageid for roles list
	create save channel for leaderboards
	send save messageid for leaderboard message
	save number of classes, number of groups within each class
	create save channel for each class
	"""

	@setup.error
	async def setup_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.reply("Only admins.")
