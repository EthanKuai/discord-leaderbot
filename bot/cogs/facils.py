import discord
from discord.ext import commands
from discord.utils import get
import json
import asyncio

from bot import *


class FacilCog(commands.Cog):
	"""For quests & competitions. Check quest-details.json and competition-details.json"""

	def __init__(self, bot: commands.bot, db: db_accessor):
		self.bot = bot
		self.db = db
		self._read_data()
		self.state = True


	async def get_msgs(self, ctx):
		# leaderboards message
		if self.db.MESSAGE_LEADERBOARDS != 0:
			_ = ctx.guild.get_channel(int(self.db.CHANNEL_LEADERBOARDS))
			self.leaderboards_msg = await _.fetch_message(int(self.db.MESSAGE_LEADERBOARDS))
		else:
			self.leaderboards_msg = None

		# facil trophy messages
		self.facil_trophy_msgs = []
		for i, msg_id in enumerate(self.db.MESSAGE_FACILS_TROPHIES):
			_ = ctx.guild.get_channel(int(self.db.CHANNEL_FACILS[i]))
			self.facil_trophy_msgs.append(await _.fetch_message(msg_id))


	def _read_data(self):
		with open('bot/data/competition-details.json') as f: self.competitions = json.load(f)["competitions"]
		with open('bot/data/quest-details.json') as f: self.quests = json.load(f)["quests"]


	async def display_leaderboards(self):
		pass


	async def display_details(self, ctx_tmp,class_nos=None):
		if self.state:
			self.state = False
			await self.get_msgs(ctx_tmp) # read msgs from db

		# msgs of all display_details messages, to edit in the future
		new_message = len(self.msgs) == 0
		if not new_message: assert len(self.msgs) == self.db.N_CLASSES

		if class_nos is None: class_nos = [i for i in range(1,1+self.db.N_CLASSES)]
		elif type(class_nos) == int: class_nos = [class_nos]
		for class_no in class_nos:
			embed = discord.Embed(title=f"40{class_no}'s trophies")
			tmp = self.db.scoreboard[self.db.scoreboard["class"]==class_no]

			# add fields in embed for quests
			for quest_no, quest in enumerate(self.quests):
				quest_no += 1
				if len(quest['points']):
					trophies = ','.join([str(_) for _ in quest['points']])
				else:
					trophies = 'varies'
				lst = []
				for j in range(self.db.N_GROUPS):
					if quest_trophies := int(tmp[tmp["group"]==chr(65+j)]["Q"+str(quest_no)]): # nonzero
						lst.append(str(class_no) + chr(65+j) + ' ' + str(quest_trophies))
					else:
						lst.append(str(class_no) + chr(65+j) + ' ❎')
				embed = embed.add_field(
					name = f"Quest {quest_no}. {quest['name']}",
					value = f"*{quest['description']}*\nTrophies: {trophies}\n{' **|** '.join(lst)}",
					inline = False
				)

			# add fields in embed for competitions
			for comp_no, comp in enumerate(self.competitions):
				comp_no += 1
				if comp_score := int(tmp[tmp["group"]=="A"]["C"+str(comp_no)]): # nonzero
					xx = "Score: " + str(comp_score)
				else:
					xx = 'Unplayed ❎'
				embed = embed.add_field(
					name = f"Defence {comp_no}. {comp['name']}",
					value = f"*{comp['description']}*\nTrophies by ranking: {','.join([str(_) for _ in comp['points']])}\n{xx}",
					inline = False
				)

			# send message
			if new_message: # new message
				ctx = self.bot.get_channel(int(self.db.CHANNEL_FACILS[class_no-1]))
				self.facil_trophy_msgs.append(await ctx.send(embed = embed))
			else: # edit existing message
				await self.facil_trophy_msgs[class_no-1].edit(embed=embed)

		if new_message:
			# save to db
			self.db.MESSAGE_FACILS_TROPHIES = [msg.id for msg in self.facil_trophy_msgs]
			self.db.save_server_data()


	@commands.command()
	@check_server()
	async def quest(self, ctx, which: int, value: int = 0):
		"""Update quest trophies"""
		user = ctx.message.author
		channelid = ctx.message.channel.id
		await ctx.message.delete()

		# check valid channel
		if channelid not in self.db.CHANNEL_FACILS:
			await ctx.send("Wrong channel! Please use the dedicated class channels.", delete_after=10)
			return
		class_no = self.db.CHANNEL_FACILS.index(channelid)+1

		# check valid class role
		if get(user.roles, name=str(class_no)) is None:
			await ctx.send("Only facils of this channel's class can use this channel!", delete_after=10)
			return

		# check for group role
		group_no = None
		for i in range(self.db.N_GROUPS):
			if get(user.roles, name=chr(65+i)) is not None:
				group_no = i+1
		if group_no is None:
			await ctx.send("You do not have any group roles! Please go to the dedicated role assigning channel and use `.role <group role>`.", delete_after=10)
			return

		# check valid quest number
		if which < 1 or which > len(self.quests):
			await ctx.send("Invalid quest number. Use `.quest <quest no.> <trophies>` to update trophies for specific quest.", delete_after=10)
			return

		# update scoreboard & save locally
		self.db.scoreboard.at[(class_no-1)*self.db.N_GROUPS+group_no-1, "Q"+str(which)] = value
		self.db.save_scoreboard()
		await self.display_details(ctx,class_no)


	@commands.command()
	@check_server()
	async def defence(self, ctx, which: int, score: int = 0):
		"""Update defence score"""
		user = ctx.message.author
		channelid = ctx.message.channel.id
		await ctx.message.delete()

		# check valid channel
		if channelid not in self.db.CHANNEL_FACILS:
			await ctx.send("Wrong channel! Please use the dedicated class channels.", delete_after=10)
			return
		class_no = self.db.CHANNEL_FACILS.index(channelid)+1

		# check valid class role
		if get(user.roles, name=str(class_no)) is None:
			await ctx.send("Only facils of this channel's class can use this channel!", delete_after=10)
			return

		# check valid defence number
		if which < 1 or which > len(self.competitions):
			await ctx.send("Invalid defence number. Use `.defence <defence no.> <score>` to update score for specific defence. Do note score is NOT trophies, and trophies will isntead be decided by relative ranking to other classes", delete_after=10)
			return

		# update scoreboard & save locally
		self.db.scoreboard.loc[(class_no-1)*self.db.N_GROUPS:class_no*self.db.N_GROUPS-1, "C"+str(which)] = score
		self.db.save_scoreboard()
		await self.display_details(ctx,class_no)
