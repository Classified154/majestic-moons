import disnake
from dataclasses import dataclass

from disnake import MessageInteraction
from disnake.ext import commands


TICK = "✅"
CROSS = "❌"


@dataclass
class Player:
	pass


class ChessBoard:
	def __init__(self):
		pass

	def __repr__(self) -> str:
		return f""

	def __str__(self) -> str:
		return ""


class GameFlow:
	def __init__(self):
		self._players: list[Player] = []
		self._chess_board: ChessBoard = ChessBoard()

	@property
	def player_one(self) -> Player:
		"""Return Player 1"""
		return self._players[0]

	@property
	def player_two(self) -> Player:
		"""Return Player 2"""
		return self._players[1]


games: list[GameFlow] = []


class MainView(disnake.ui.View):
	def __init__(self):
		super().__init__(timeout=None)

	async def interaction_check(self, inter: MessageInteraction) -> bool:
		return inter.author.guild_permissions.manage_messages

	async def on_error(self, error: Exception, item: disnake.ui.Item, inter: MessageInteraction):
		await inter.response.send_message("Pleas wait for your turn!")

	@disnake.ui.button(label="Play Turn", emoji=CROSS, style=disnake.ButtonStyle.grey, custom_id="ticket_close")
	async def close_ticket(self, button: disnake.Button, inter: disnake.MessageInteraction):
		"""Button to play your turn"""
		# TODO Complete play button


class ChessCog(commands.Cog):

	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.persistence_views = False

	async def cog_load(self):
		await self.bot.wait_until_ready()

		"""To load data from sqlite if needed"""

	@commands.Cog.listener()
	async def on_ready(self):
		if self.persistence_views is False:
			self.bot.add_view(MainView())

			self.persistence_views = True

		await self.bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.playing, name="with tickets"))

	@commands.slash_command()
	@commands.default_member_permissions(administrator=True)
	async def game(self, inter: disnake.CommandInteraction, opponent: disnake.Member):
		"""
		Start your game

		Parameters
		----------
		opponent: Mention a user you want to play with
		"""
		await inter.response.send("Nothing yet!")


class ConfirmDelete(disnake.ui.View):
	def __init__(self, author_id):
		super().__init__(timeout=None)
		self.author_id = author_id
		self.confirm = False

	async def interaction_check(self, inter):
		return inter.author.id == self.author_id

	@disnake.ui.button(emoji=TICK, style=disnake.ButtonStyle.secondary)
	async def confirm_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
		text = f"Confirmed {TICK}"
		self.confirm = True
		self.clear_items()

		await interaction.response.edit_message(text, view=self)
		self.stop()

	@disnake.ui.button(emoji=CROSS, style=disnake.ButtonStyle.secondary)
	async def rejection_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
		text = f"Rejected {CROSS}"
		self.confirm = False
		self.clear_items()

		await interaction.response.edit_message(text, view=self)
		self.stop()


def setup(bot):
	bot.add_cog(ChessCog(bot))
	print("[ChessGame] Loaded")
