import os
import json
from pandas import read_csv
from datetime import datetime


class db_accessor:
	"""Accesses data files."""

	def __init__(self):
		try:
			with open("TOKEN") as f: self.TOKEN = f.readline().strip()
			self.read_server_data()
			self.read_scoreboard()
		except Exception as e:
			print("db.__init__: Failed to read data\n",e)
			exit()


	def read_scoreboard(self):
		self.scoreboard = read_csv("bot/data/scores.csv")


	def reset_scoreboard(self):
		self.scoreboard = read_csv("bot/data/scores-default.csv")
		os.rename("bot/data/scores.csv", "bot/data/scores"+str(datetime.now()).replace(":","-")+".csv")
		self.save_scoreboard()


	def save_scoreboard(self):
		self.scoreboard.to_csv("bot/data/scores.csv", index = False)


	def read_server_data(self):
		self.server_vars = []
		with open('bot/data/server-details.json') as f:
			data = json.load(f)
			for key, val in data.items():
				self.server_vars.append(key)
				if type(val) == str: exec(f'self.{key} = "{val}"')
				else: exec(f'self.{key} = {val}')


	def save_server_data(self):
		dct = {}
		for key in self.server_vars:
			dct[key] = eval(f"self.{key}")
		with open('bot/data/server-details.json', 'w') as f:
			json.dump(dct, f)


	def update_data(self):
		"""Overwrite all data in database with current data."""
		try:
			self.save_scoreboard()
			self.save_server_data()
		except:
			print("db.update_data: Failed to update data")
			exit()
		else:
			return True
