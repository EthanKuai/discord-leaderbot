import asyncio
from discord.ext import commands


MANAGER_ROLE = "Manager" # name of manager role
local_bot = None # bot
local_db = None # db


def setup_checks(bot, db):
	"""run at startup"""
	global local_bot
	global local_db
	local_bot = bot
	local_db = db


"""Checks to be used for discord bot commands"""


def confirmation(*, emoji: str = "✅", timeout: int = 30):
	"""Sends confirmation message to user to react before proceeding."""
	async def inner_fn(ctx):
		global local_bot

		# send embed, add ✅ emoji reaction
		msg = await ctx.reply("React " + emoji + " to confirm.")
		await msg.add_reaction(emoji)

		# detect for user's reaction
		def check(reaction, user):
			return str(reaction)==emoji and user.id==ctx.message.author.id
		try:
			reaction = None
			reaction, _ = await local_bot.wait_for('reaction_add', timeout=timeout, check=check)
		except asyncio.TimeoutError: # timeout
			await msg.add_reaction("❎")
		finally:
			await msg.delete()
			return reaction is not None
	return commands.check(inner_fn)


def check_server():
	def inner_fn(ctx):
		global local_db
		return ctx.guild.id==local_db.GUILD_ID
	return commands.check(inner_fn)


def check_manager():
	def inner_fn(ctx):
		return ctx.guild.owner_id==ctx.author.id
	return commands.check_any(commands.has_role(MANAGER_ROLE), inner_fn)


def check_owner():
	def inner_fn(ctx):
		return ctx.guild.owner_id==ctx.author.id
	return commands.check(inner_fn)


def check_role_channel():
	def inner_fn(ctx):
		global local_db
		return int(ctx.channel.id)==int(local_db.CHANNEL_ROLES)
	return commands.check(inner_fn)
