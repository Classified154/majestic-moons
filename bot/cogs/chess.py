from dataclasses import dataclass

import disnake
from disnake import MessageInteraction
from disnake.ext import commands

TICK = "✅"
CROSS = "❌"


@dataclass
class Player:
    """Player class."""


class ChessBoard:
    """Chess Board class."""

    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        return ""

    def __str__(self) -> str:
        return ""


class GameFlow:
    """Game Flow class."""

    def __init__(self) -> None:
        self._players: list[Player] = []
        self._chess_board: ChessBoard = ChessBoard()

    @property
    def player_one(self) -> Player:
        """Return Player 1."""
        return self._players[0]

    @property
    def player_two(self) -> Player:
        """Return Player 2."""
        return self._players[1]


games: list[GameFlow] = []


class MainView(disnake.ui.View):
    """Main View class."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def interaction_check(self, inter: MessageInteraction) -> bool:
        """Check if the interaction is valid."""
        return inter.author.guild_permissions.manage_messages

    async def on_error(self, _: Exception, __: disnake.ui.Item, inter: MessageInteraction) -> None:
        """Error handler."""
        await inter.response.send_message("Pleas wait for your turn!")

    @disnake.ui.button(label="Play Turn", emoji=CROSS, style=disnake.ButtonStyle.grey, custom_id="ticket_close")
    async def close_ticket(self, button: disnake.Button, inter: disnake.MessageInteraction) -> None:
        """Button to play your turn."""
        # Complete play button


class ChessCog(commands.Cog):
    """Chess Cog class."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.persistence_views = False

    async def cog_load(self) -> None:
        """When the cog is loaded."""
        await self.bot.wait_until_ready()

        """To load data from sqlite if needed"""

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """When the bot is ready."""
        if self.persistence_views is False:
            self.bot.add_view(MainView())

            self.persistence_views = True

        await self.bot.change_presence(
            activity=disnake.Activity(type=disnake.ActivityType.playing, name="with chess pieces"),
        )

    @commands.slash_command()
    @commands.default_member_permissions(administrator=True)
    async def game(self, inter: disnake.CommandInteraction, opponent: disnake.Member) -> None:  # noqa: D417
        """Start your game.

        Parameters
        ----------
        opponent: Mention a user you want to play with.

        """
        print(opponent)
        await inter.response.send("Nothing yet!")


class ConfirmDelete(disnake.ui.View):
    """Confirm Delete class."""

    def __init__(self, author_id: int) -> None:
        super().__init__(timeout=None)
        self.author_id = author_id
        self.confirm = False

    async def interaction_check(self, inter: disnake.MessageInteraction) -> None:
        """Check if the interaction is valid."""
        return inter.author.id == self.author_id

    @disnake.ui.button(emoji=TICK, style=disnake.ButtonStyle.secondary)
    async def confirm_button(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        """Confirm button."""
        text = f"Confirmed {TICK}"
        self.confirm = True
        self.clear_items()

        await interaction.response.edit_message(text, view=self)
        self.stop()

    @disnake.ui.button(emoji=CROSS, style=disnake.ButtonStyle.secondary)
    async def rejection_button(self, _: disnake.ui.Button, interaction: disnake.MessageInteraction) -> None:
        """Reject button."""
        text = f"Rejected {CROSS}"
        self.confirm = False
        self.clear_items()

        await interaction.response.edit_message(text, view=self)
        self.stop()


def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot."""
    bot.add_cog(ChessCog(bot))
    print("[ChessGame] Loaded")
