import discord
from discord.ext import commands

from bot import *
import sys


class OwnerCog(commands.Cog):
	"""Debugging commands only for owner :)"""

	def __init__(self, bot: commands.bot, db: db_accessor):
		self.bot = bot
		self.db = db

	# Won't show up on the default help.
	@commands.command(name='_load', hidden=True)
	@commands.is_owner()
	async def load_cog(self, ctx, cog: str):
		"""Load cog, cog name requires full path"""
		try:
			self.bot.load_extension(cog)
		except Exception as e:
			await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
		else:
			await ctx.send('**`SUCCESS`**')


	@commands.command(name='_unload', hidden=True)
	@commands.is_owner()
	async def unload_cog(self, ctx, cog: str):
		"""Unload cog, cog name requires full path"""
		try:
			self.bot.unload_extension(cog)
		except Exception as e:
			await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')
		else:
			await ctx.send('**`SUCCESS`**')


	@commands.command(name='_reload', hidden=True)
	@commands.is_owner()
	async def reload_cog(self, ctx, cog: str):
		"""Reload cog for debugging, cog name requires full path"""
		await self.load_cog(ctx, cog)
		await self.unload_cog(ctx, cog)


	@commands.command(name='_embed', hidden=True)
	@commands.is_owner()
	async def send_embed(self, ctx, *, arg: str):
		"""Input dictionary args for embed message"""
		try:
			if arg.startswith('discord.Embed'):
				await ctx.send(embed = eval(arg))
			else:
				await ctx.send(embed = eval(f'discord.Embed({arg})'))
		except:
			await ctx.send("failed.")


	@commands.command(name='_error', hidden=True)
	@commands.is_owner()
	async def debug_error(self, ctx, *, description: str):
		"""Raises exception of stated description"""
		await ctx.send("**<Admin>** Error raised.")
		raise discord.DiscordException(description)


	@commands.command(name='_info', hidden=True)
	@commands.is_owner()
	async def debug_info(self, ctx):
		"""Various useful information"""
		try:
			out = "**<Admin>** Channel information.\n"
			out += f'**guild:**{ctx.guild}, **guild id:**{ctx.guild.id}\n'
			out += f'**channel:**{ctx.channel}, **channel id:**{ctx.channel.id}\n'
			out += '**channel list:** '
			out += " ".join([c.name for c in ctx.guild.channels]) + '\n'
			out += f'**author:**{ctx.author}, **author id :**{ctx.author.id}\n'
			out += '**member list:** '
			out += " ".join([f'({m}, {m.id})' for m in ctx.guild.members]) + '\n'
			out += f'Functions of ctx: use command `dir(ctx)`'
			await p(ctx, out)
		except:
			await ctx.send("failed.")
			await self.debug_error(ctx, description="_info failed")


	@commands.command(name='_eval', hidden=True)
	@commands.is_owner()
	async def debug_eval(self, ctx, *, arg: str):
		"""!!Warning!! Evaluates given statement"""
		try:
			await ctx.send(eval(arg))
		except:
			await ctx.send("failed.")


	@commands.command(name='_exec', hidden=True)
	@commands.is_owner()
	async def debug_exec(self, ctx, *, arg: str):
		"""!!Warning!! Executes given statement"""
		try:
			await ctx.send(exec(arg))
		except:
			await ctx.send("failed.")

	@commands.command(name='_database', hidden=True)
	@commands.is_owner()
	async def debug_database(self, ctx, *, arg: str):
		"""!!Warning!! Dumps database info"""
		try:
			if arg=="confirm": # extra preventive measure
				await p(ctx, '```' + str(vars(self.db)).replace("`","\`") + '```')
			else:
				await ctx.send("Unconfirmed! Execute this in private channel.")
		except:
			await ctx.send("failed.")
