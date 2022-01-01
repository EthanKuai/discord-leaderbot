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


	async def get_msgs_roles(self, ctx):
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

		# roles
		_ = [str(i+1) for i in range(self.db.N_CLASSES)]
		self.roles_classes = [get(ctx.guild.roles, name=n) for n in _]
		_ = [chr(65+i) for i in range(self.db.N_GROUPS)]
		self.roles_groups = [get(ctx.guild.roles, name=n) for n in _]
		self.roles = self.roles_classes + self.roles_groups


	def _read_data(self):
		with open('bot/data/competition-details.json') as f: self.competitions = json.load(f)["competitions"]
		with open('bot/data/quest-details.json') as f: self.quests = json.load(f)["quests"]


	def competition_points(self, lst: list, comp: dict):
		"""Returns & accepts [(rank, class_no, score, points)]"""
		lst = sorted(lst, key=lambda x: -x[2])
		for rank in range(1, 1+len(lst)):
			if lst[rank-1][2]==0: # havn't played
				lst[rank-1][0] = "N.A." # rank
				continue
			if rank > len(comp["points"]): # outside points range
				lst[rank-1][0] = rank # rank
				continue
			if rank>1 and lst[rank-1][2]==lst[rank-2][2]: # scored same as dude above
				lst[rank-1][3] = lst[rank-2][3] # points
				lst[rank-1][0] = lst[rank-2][0] # rank
			else: # normal
				lst[rank-1][0] = rank # rank
				lst[rank-1][3] = comp["points"][rank-1]
		return lst


	async def display_leaderboards(self, ctx_tmp):
		if self.state:
			self.state = False
			await self.get_msgs_roles(ctx_tmp) # read msgs from db

		embed = discord.Embed(title="STARVING GAMES LEADERBOARDS",color=discord.Colour.orange())

		# calc points (base + quests)
		class_points = [BASE_POINTS for i in range(self.db.N_CLASSES)]
		quest_points = [0 for i in range(self.db.N_CLASSES)]
		comp_points = [0 for i in range(self.db.N_CLASSES)]
		for class_no in range(1,1+self.db.N_CLASSES):
			_ = ["Q"+str(i+1) for i in range(len(self.quests))]
			quest_points[class_no-1] = self.db.scoreboard.loc[(class_no-1)*self.db.N_GROUPS:class_no*self.db.N_GROUPS-1,_].sum().sum()
			class_points[class_no-1] += quest_points[class_no-1]

		# add fields in embed for competitions + points
		for comp_no, comp in enumerate(self.competitions):
			comp_no += 1
			def inner_fn(score):
				if score: return score
				return '❎'

			rankings = self.competition_points([
				(0, class_no+1, self.db.scoreboard.at[class_no*self.db.N_GROUPS, "C"+str(comp_no)], 0)
				for class_no in range(self.db.N_CLASSES//2)
			], comp) # [(rank, class_no, score, points)]
			rankings_str = []
			for (rank, class_no, score, points) in rankings:
				rankings_str.append(f"**{rank}** 40{class_no} ({points} Trophies) (Score: {inner_fn(score)})")
				comp_points[class_no-1] = points
				class_points[class_no-1] += points
			embed = embed.add_field(
				name = f"Defence {comp_no}. {comp['name']}",
				value = '\n'.join(rankings_str),
				inline = False
			)

			rankings = self.competition_points([
				(0, class_no+1, self.db.scoreboard.at[class_no*self.db.N_GROUPS, "C"+str(comp_no)], 0)
				for class_no in range(self.db.N_CLASSES//2,self.db.N_CLASSES)
			], comp) # [(rank, class_no, score, points)]
			rankings_str = []
			for (rank, class_no, score, points) in rankings:
				rankings_str.append(f"**{rank}** 40{class_no} ({points} Trophies) (Score: {inner_fn(score)})")
				comp_points[class_no-1] = points
				class_points[class_no-1] += points
			embed = embed.add_field(
				name = f"Defence {comp_no}. {comp['name']}",
				value = '\n'.join(rankings_str),
				inline = False
			)

		# quest rankings
		quest_points = [(i+1, points) for i, points in enumerate(quest_points)]
		quest_points = sorted(quest_points, key=lambda x: -x[1])
		quest_points_str = [f"**{i+1}** 40{class_no} ({points} Trophies)" for i, (class_no, points) in enumerate(quest_points)]
		embed = embed.add_field(
			name = "Quest Rankings",
			value = '\n'.join(quest_points_str),
			inline = True
		)

		# competition rankings
		comp_points = [(i+1, points) for i, points in enumerate(comp_points)]
		comp_points = sorted(comp_points, key=lambda x: -x[1])
		comp_points_str = [f"**{i+1}** 40{class_no} ({points} Trophies)" for i, (class_no, points) in enumerate(comp_points)]
		embed = embed.add_field(
			name = "Defence Rankings",
			value = '\n'.join(comp_points_str),
			inline = True
		)

		# overall rankings
		class_points = [(i+1, points) for i, points in enumerate(class_points)]
		class_points = sorted(class_points, key=lambda x: -x[1])
		class_points_str = [f"**{i+1}** 40{class_no} ({points} Trophies)" for i, (class_no, points) in enumerate(class_points)]
		embed = embed.add_field(
			name = "OVERALL CLASS RANKINGS",
			value = '\n'.join(class_points_str),
			inline = True
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
			await self.get_msgs_roles(ctx_tmp) # read msgs from db

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
		if self.roles_classes[class_no-1] not in user.roles[1:]:
		#if get(user.roles, name=str(class_no)) is None:
			await ctx.send("Only facils of this channel's class can use this channel!", delete_after=10)
			return

		# check for group role
		grouproles = [role for role in user.roles[1:] if role in self.roles_groups]
		if len(grouproles) == 0:
			await ctx.send("You do not have any group roles! Please go to the dedicated role assigning channel and use `.role <group role>` to add/remove roles. E.g. `.role A`", delete_after=10)
			return
		if len(grouproles) > 1:
			await ctx.send("You have more than one group roles! Please go to the dedicated role assigning channel and use `.role <group role>` to remove the extra roles. E.g. `.role A`", delete_after=10)
			return
		group_no = ord(grouproles[0])-64

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
		if self.roles_classes[class_no-1] not in user.roles[1:]:
		#if get(user.roles, name=str(class_no)) is None:
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


	@commands.command()
	@check_server()
	@check_manager()
	@confirmation()
	async def reset(self, ctx):
		"""Manager: resets game (scores, points, leaderboards, roles)"""
		self.db.reset_scoreboard()
		await self.display_details(ctx)
		await self.display_leaderboards(ctx)
		await self.remove_roles(ctx)
		await ctx.reply("Game reset!")


	async def remove_roles(self, ctx):
		"""Remove roles from everyone"""
		async for member in ctx.guild.fetch_members(limit=None):
			roles_to_remove = (role for role in member.roles[1:] if role in self.roles)
			await member.remove_roles(*roles_to_remove)
