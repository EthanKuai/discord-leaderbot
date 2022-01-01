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
	async def role(self, ctx, *, roles: str):
		"""Adds/removes class & group roles for yourself, separated by commas."""
		roles = roles.split(',')
		user = ctx.message.author
		desc = "**Roles added/removed**:\n"

		try:
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

			await ctx.message.delete()
			out_msg = discord.Embed(description=desc+"*P.S. Role names are case sensitive.*").set_footer(text=str(ctx.author),icon_url=ctx.author.avatar_url)
			await ctx.send(ctx.message.author.mention, embed=out_msg, delete_after=10)
		except:
			await ctx.send("Admins have to create gorup & class roles to be lower priority than mine's.")
