import os


class db_accessor:
	"""Accesses environmental variables."""

	def __init__(self):
		self._ENV_LST = ['TOKEN','GUILD_ID','CHANNEL_ROLES','CHANNEL_LEADERBOARDS','MESSAGE_ROLES_LIST']
		try:
			for i in self._ENV_LST:
				exec(f'self.{i} = os.environ["{i}"]')
				if eval(f'self.{i}').isnumeric(): exec(f'self.{i} = int(self.{i})')
		except Exception as e:
			print("db.__init__: Failed to read environmental variables & database")
			print(e)
			exit()


	def add_variable(self, name: str, val, strval: str = ""):
		"""!!!ASSUMES SANITIZED VARIABLE 'name'!!!
		Adds variable to ENV, but not be auto-loaded once program restarts."""
		try:
			assert not (name in self.__dict__) # make sure variable does not already exist
			if strval == "": strval = str(val)

			self._ENV_LST.append(name)
			exec(f'self.{name} = val')
			os.environ[name] = strval
		except:
			print("db.add_variable: Failed")
		else:
			return True


	def update_data(self):
		"""Overwrite all data in database with current data."""
		try:
			for i in self._ENV_LST: os.environ[i] = str(eval(f'self.{i}'))
		except:
			print("db.update_data: Failed to update environmental variables")
			exit()
		else:
			return True
