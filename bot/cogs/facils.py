import discord
from discord.ext import commands
from discord.utils import get
import json
import asyncio

from bot import *
BASE_POINTS = 1000


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


	def competition_points(self, comp: dict, rank: int, score: int):
		if score==0: return 0 # havn't played
		if rank > len(comp["points"]): return 0 # outside of award range
		return comp["points"][rank-1]


	async def display_leaderboards(self, ctx_tmp):
		if self.state:
			self.state = False
			await self.get_msgs(ctx_tmp) # read msgs from db

		embed = discord.Embed(title="STARVING GAMES LEADERBOARDS",color=discord.Colour.orange())

		# calc points (base + quests)
		class_points = [BASE_POINTS for i in range(self.db.N_CLASSES)]
		for class_no in range(1,1+self.db.N_CLASSES):
			_ = ["Q"+str(i+1) for i in range(len(self.quests))]
			class_points[class_no-1] += self.db.scoreboard.loc[(class_no-1)*self.db.N_GROUPS:class_no*self.db.N_GROUPS-1,_].sum().sum()

		# add fields in embed for competitions + points
		for comp_no, comp in enumerate(self.competitions):
			comp_no += 1
			def inner_fn(score):
				if score: return score
				return '❎'
			rankings = [
				(class_no+1, self.db.scoreboard.at[class_no*self.db.N_GROUPS, "C"+str(comp_no)])
				for class_no in range(self.db.N_CLASSES//2)
			]
			rankings = sorted(rankings, key=lambda x: -x[1])
			rankings_str = []
			for i, (class_no, score) in enumerate(rankings):
				rankings_str.append(f"**{i+1}** 40{class_no} (Score: {inner_fn(score)})")
				class_points[class_no-1] += self.competition_points(comp, i+1, score)
			embed = embed.add_field(
				name = f"Defence {comp_no}. {comp['name']}",
				value = '\n'.join(rankings_str),
				inline = True
			)

			rankings = [
				(class_no+1, self.db.scoreboard.at[class_no*self.db.N_GROUPS, "C"+str(comp_no)])
				for class_no in range(self.db.N_CLASSES//2,self.db.N_CLASSES)
			]
			rankings = sorted(rankings, key=lambda x: -x[1])
			rankings_str = []
			for i, (class_no, score) in enumerate(rankings):
				rankings_str.append(f"**{i+1}** 40{class_no} (Score: {inner_fn(score)})")
				class_points[class_no-1] += self.competition_points(comp, i+1, score)
			embed = embed.add_field(
				name = f"Defence {comp_no}. {comp['name']}",
				value = '\n'.join(rankings_str),
				inline = False
			)

		# overall ranking
		class_points = [(i+1, points) for i, points in enumerate(class_points)]
		class_points = sorted(class_points, key=lambda x: -x[1])
		class_points_str = [f"**{i+1}** 40{class_no} (Trophies: {points})" for i, (class_no, points) in enumerate(class_points)]
		embed = embed.add_field(
			name = "OVERALL CLASS RANKINGS",
			value = '\n'.join(class_points_str),
			inline = False
		)

		# send message
		if self.leaderboards_msg is None: # new message
			ctx = ctx_tmp.guild.get_channel(int(self.db.CHANNEL_LEADERBOARDS))
			self.leaderboards_msg = await ctx.send(embed=embed)
			# save to db
			self.db.MESSAGE_LEADERBOARDS = self.leaderboards_msg.id
			self.db.save_server_data()
		else: # edit existing message
			await self.leaderboards_msg.edit(embed=embed)


	async def display_details(self, ctx_tmp, class_nos=None):
		if self.state:
			self.state = False
			await self.get_msgs(ctx_tmp) # read msgs from db

		# msgs of all display_details messages, to edit in the future
		new_message = len(self.facil_trophy_msgs) == 0
		if not new_message: assert len(self.facil_trophy_msgs) == self.db.N_CLASSES

		if class_nos is None: class_nos = [i for i in range(1,1+self.db.N_CLASSES)]
		elif type(class_nos) == int: class_nos = [class_nos]
		for class_no in class_nos:
			embed = discord.Embed(title=f"40{class_no}'s trophies",color=discord.Colour.green())
			#tmp = self.db.scoreboard[self.db.scoreboard["class"]==class_no]

			# add fields in embed for quests
			for quest_no, quest in enumerate(self.quests):
				quest_no += 1
				if len(quest['points']):
					trophies = ','.join([str(_) for _ in quest['points']])
				else:
					trophies = 'varies'
				lst = []
				for j in range(self.db.N_GROUPS):
					#if quest_trophies := int(tmp[tmp["group"]==chr(65+j)]["Q"+str(quest_no)]): # nonzero
					if quest_trophies := self.db.scoreboard.at[(class_no-1)*self.db.N_GROUPS+j, "Q"+str(quest_no)]: # nonzero
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
				#if comp_score := int(tmp[tmp["group"]=="A"]["C"+str(comp_no)]): # nonzero
				if comp_score := self.db.scoreboard.at[(class_no-1)*self.db.N_GROUPS, "C"+str(comp_no)]: # nonzero
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
		await self.display_leaderboards(ctx)


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
		await self.display_leaderboards(ctx)
