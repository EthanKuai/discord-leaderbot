import discord
from discord.ext import commands
from discord.utils import get

from bot import *


class RoleCog(commands.Cog):
	"""Creates & allows users to add specific roles."""

	def __init__(self, bot: commands.bot, db: db_accessor):
		self.bot = bot
		self.db = db
		assert self.db.N_GROUPS < 26
		self.valid_roles = [chr(65+i) for i in range(self.db.N_GROUPS)] + [str(i+1) for i in range(self.db.N_CLASSES)]


	@commands.command()
	@check_server()
	@check_role_channel()
	async def role(self, ctx, *, roles: str):
		"""Adds/removes class & group roles for yourself, separated by commas."""
		roles = roles.split(',')
		user = ctx.message.author
		desc = "**Roles added/removed**:\n"

		try:
			await ctx.message.delete()
			for role_str in roles:
				role_str = role_str.strip()
				if role_str in self.valid_roles:
					role_obj = get(user.guild.roles, name=role_str)
					if get(user.roles, name=role_str) is None: # do not currently have role, so add
						await user.add_roles(role_obj)
						desc += f"{role_str}: ✅ Added\n"
					else: # already has role, so remove
						await user.remove_roles(role_obj)
						desc += f"{role_str}: ✅ Removed\n"
				else:
					tmp = role_str.replace('*','\*').replace('_','\_')
					desc += f"{tmp}: ❎ Wrong name!\n"

			desc += "\n**Current roles:** " + ', '.join([str(i) for i in user.roles[1:]])
			desc += "\n*P.S. Role names are case sensitive.*"
			out_msg = discord.Embed(description=desc).set_footer(text=str(ctx.author),icon_url=ctx.author.avatar_url)
			await ctx.send(ctx.message.author.mention, embed=out_msg, delete_after=10)
		except:
			await ctx.send("Admins have to create gorup & class roles to be lower priority than mine's.")


	@role.error
	async def role_error(self, ctx, error):
		if isinstance(error, commands.CheckFailure):
			await ctx.message.delete()
			await ctx.send("Wrong channel. Go to "+self.bot.get_channel(self.db.CHANNEL_ROLES).mention, delete_after=10)
