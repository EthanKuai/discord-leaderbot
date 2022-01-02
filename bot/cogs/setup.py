import discord
from discord.ext import commands

from bot import *


class SetupCog(commands.Cog):
	"""In charge of setting up the server"""

	def __init__(self, bot: commands.bot, db: db_accessor):
		self.bot = bot
		self.db = db


	@commands.command()
	@check_owner()
	@confirmation()
	async def setup(self, ctx, n_classes: int, n_groups: int):
		"""Setup the full server for game, only usable by an admin. First give the bot admin perms."""
		# guild
		guild = ctx.guild
		self.db.GUILDID = guild.id
		overwrites = {
			guild.default_role: discord.PermissionOverwrite(send_messages=False)
		}

		# create category
		category_admin = await guild.create_category("ADMIN")
		category_classes = await guild.create_category("CLASSES")
		await ctx.send("Created categories")

		# roles channel
		channel_roles = await guild.create_text_channel("assign-roles", category=category_admin)
		self.db.CHANNEL_ROLES = channel_roles.id
		with open("bot/data/channel_roles_message.txt") as f: msg_roles = f.read()
		await channel_roles.send(msg_roles)
		await ctx.send("Created roles channel")

		# leaderboards channel
		channel_leaderboards = await guild.create_text_channel("leaderboards", category=category_admin, overwrites=overwrites)
		self.db.CHANNEL_LEADERBOARDS = channel_leaderboards.id
		await ctx.send("Created leaderboards channel")

		# classes channels
		self.db.N_CLASSES = n_classes
		self.db.N_GROUPS = n_groups
		channel_classes = [await guild.create_text_channel("40"+str(i+1), category=category_classes) for i in range(n_classes)]
		self.db.CHANNEL_FACILS = channel_classes
		await ctx.send("Created classes' channels")

		# announcements channel
		channel_announcements = await guild.create_text_channel("announcements", category=category_admin, overwrites=overwrites)
		with open("bot/data/channel_announcements_message.txt") as f: msg_announcements = eval(f.read())
		await channel_announcements.send(msg_announcements)
		await ctx.send("Created announcements channel")

		# create roles
		lst = [str(i+1) for i in range(n_classes)] + [chr(65+i) for i in range(n_groups)]
		for i in lst: await guild.create_role(name=i)
		manager_role = await guild.create_role(name="Manager")
		await ctx.author.add_roles(manager_role)
		await ctx.send("Created roles")

		# save
		self.db.save_server_data()


	@commands.command()
	@check_manager()
	@confirmation()
	@check_server()
	async def roles(self, ctx):
		pass

	"""
	save guildid
	create channel for roles
	send save messageid for roles list
	create save channel for leaderboards
	send save messageid for leaderboard message
	save number of classes, number of groups within each class
	create save channel for each class
	create leaderboards file
	"""

	@setup.error
	async def setup_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.reply("Only admins.")
