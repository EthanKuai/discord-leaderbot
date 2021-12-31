import discord
from discord.ext import commands

from bot import *
from .cogs import *
from .keep_alive import alive


# bot
help_command = commands.DefaultHelpCommand(no_category = 'Others')

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.typing = False
intents.presences = False

bot = commands.Bot(
	command_prefix = commands.when_mentioned_or('.'),
	description = "Orientation discord bot. Type `.help` for more info.",
	intents = intents,
	case_insensitive = True,
	help_command = help_command
)


# cogs
db = db_accessor()

bot_cogs = {
	'owner':OwnerCog(bot, db),
	'competition':CompetitionCog(bot, db),
	'quest':QuestCog(bot, db),
	'manager':ManagerCog(bot, db),
	'setup':SetupCog(bot, db),
	'roles':RoleCog(bot, db)
}


# bot commands
@bot.event
async def on_ready():
	"""When bot is ready and connected to Discord"""
	await bot.change_presence(activity=discord.Game(name='Type .help for help!', type=1))
	print(f'{bot.user.name=}; {bot.user.id=}; {discord.__version__=}')

@bot.command()
async def ping(ctx):
	await ctx.send("pong.")


# main script
def main():
	global bot
	for bot_cog in bot_cogs.values(): bot.add_cog(bot_cog)
	setup_checks(bot, db)
	alive()
	bot.run(db.TOKEN, bot=True, reconnect=True)

if __name__ == '__main__':
	main()
