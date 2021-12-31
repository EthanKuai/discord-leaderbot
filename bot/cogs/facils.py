import discord
from discord.ext import commands
from discord.utils import get
import json

from bot import *


class FacilCog(commands.Cog):
	"""For quests & competitions. Check quest-details.json and competition-details.json"""

	def __init__(self, bot: commands.bot, db: db_accessor):
		self.bot = bot
		self.db = db
		self._read_data()
		self.msgs = []


	def _read_data(self):
		with open('bot/data/competition-details.json') as f: self.competitions = json.load(f)["competitions"]
		with open('bot/data/quest-details.json') as f: self.quests = json.load(f)["quests"]


	async def display_details(self):
		# msgs of all display_details messages, to edit in the future
		new_message = len(self.msgs) == 0
		if not new_message: assert len(self.msgs) == self.db.N_CLASSES

		for class_no in range(1,1+self.db.N_CLASSES):
			embed = discord.Embed(title=f"40{class_no}'s trophies")
			tmp = self.db.scoreboard[self.db.scoreboard["class"]==i]

			# add fields in embed for quests
			for quest_no, quest in enumerate(self.quests):
				quest_no += 1
				if len(quest['points']):
					trophies = ','.join(quest['points'])
				else:
					trophies = 'varies'
				lst = []
				for j in range(self.db.N_GROUPS):
					if quest_trophies := int(tmp[tmp["group"]==chr(65+j)]["Q"+str(quest_no)]): # nonzero
						lst.append(str(class_no) + chr(65+j) + ' ' + str(quest_trophies))
					else:
						lst.append(str(class_no) + chr(65+j) + ' ❎')
				embed = embed.add_field(
					name = f"{quest_no}. {quest['name']}",
					value = f"*{quest['description']}*\n*Trophies*: {trophies}\n{'|'.join(lst)}",
					inline = False
				)

			# add fields in embed for competitions
			for comp_no, comp in enumerate(self.competitions):
				comp_no += 1
				lst = []
				for j in range(self.db.N_GROUPS):
					if comp_score := int(tmp[tmp["group"]==chr(65+j)]["C"+str(comp_no)]): # nonzero
						lst.append(str(class_no) + chr(65+j) + ' ' + str(comp_score))
					else:
						lst.append(str(class_no) + chr(65+j) + ' ❎')
				embed = embed.add_field(
					name = f"{comp_no}. {comp['name']}",
					value = f"*{comp['description']}*\n*Trophies by ranking*: {','.join(comp['points'])}\n{'|'.join(lst)}",
					inline = False
				)

			# send message
			if new_message: # new message
				channelid = int(tmp[tmp["group"]=="A"]["channel"])
				channel = self.bot.get_channel(channelid)
				self.msgs.append(await channel.send(embed = embed))
			else: # edit existing message
				await self.msgs[class_no-1].edit(embed=embed)


	@commands.command()
	@check_server()
	async def quest(self, ctx, which: int, value: int = 0):
		"""Display list of quests & details, according to facil's assigned class & group"""
		user = ctx.message.author
		channelid = ctx.message.channel.id

		# check valid channel
		tmp = self.db.scoreboard[self.db.scoreboard["channel"]==channelid]
		if len(tmp) == 0:
			await ctx.send("Wrong channel! Please use the dedicated class channels.", delete_after=10)
			return
		class_no = int(tmp['class'][0])

		# check valid class role
		if get(user.roles, name=str(class_no)) is None:
			await ctx.send("Only facils of this channel's class can use this channel!", delete_after=10)
			return

		# check for group role
		group = None
		for i in range(self.db.N_GROUPS):
			if get(user.roles, name=chr(65+i)) is not None:
				group = chr(65+i)
		if group is None:
			await ctx.send("You do not have any group roles! Please go to the dedicated role assigning channel and use `.role <group role>`.", delete_after=10)
			return

		# check valid quest number
		if which < 1 or which > len(self.quests):
			await ctx.send("Invalid quest number. Use `.quest <quest no.> <trophies>` to update trophies for specific quest.", delete_after=10)
			return

		# update scoreboard & save locally
		tmp[tmp["group"]==group]["Q"+str(which)] = value
		self.db.save_scoreboard()
		await self.display_details()
		await ctx.send("hi")
