import asyncio
import random
from dataclasses import dataclass
from enum import Enum

import disnake
from disnake import MessageInteraction
from disnake.ext import commands

TICK = "✅"
CROSS = "❌"


class TileStatus(Enum):
    """Tile Status class."""

    EMPTY = 0
    FILLED = 1


@dataclass
class Player:
    """Player class."""


class Dot:
    """Dot class."""

    def __init__(self, num: int) -> None:
        self._num = num
        self._found: bool = False

    def __repr__(self) -> str:
        return f"Dot(Number:{self._num}, Found:{self._found})"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def num(self) -> int:
        """Return the number."""
        return self._num

    @property
    def found(self) -> bool:
        """Return if the dot is found."""
        return self._found

    @found.setter
    def found(self, value: bool) -> None:
        self._found = value


class Tile:
    """Tile class."""

    def __init__(self, num: int, empty: TileStatus) -> None:
        self._num = num
        self._empty: TileStatus = empty

    def __repr__(self) -> str:
        return f"Tile(Number:{self._num})"

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def is_empty(self) -> bool:
        """Return if the tile is empty."""
        return self._empty == TileStatus.EMPTY


class EmptyTile(Tile):
    """Empty Tile class."""

    def __init__(self, num: int) -> None:
        super().__init__(num, TileStatus.EMPTY)

    def __repr__(self) -> str:
        return "EmptyTile(Empty:True)"


class ActiveTile(Tile):
    """Tile class."""

    def __init__(self, num: int, dots_num: list[int]) -> None:
        super().__init__(num, TileStatus.FILLED)
        self._dots: list[Dot] = [Dot(i) for i in dots_num]

    def __repr__(self) -> str:
        return f"Tile(Dots:{self._dots})"

    def __iter__(self) -> iter:
        return iter(self._dots)

    def __getitem__(self, index: int) -> Dot:
        return self._dots[index]

    def __len__(self) -> int:
        return len(self._dots)

    def set_dot_found(self, position: int) -> None:
        """Mark a dot as found."""
        self._dots[position].found = True

    def show_dot_found(self) -> list[Dot]:
        """Show the dots that are found."""
        return [dot for dot in self._dots if dot.found]


class Board:
    """Board class."""

    def __init__(self, board_size: tuple[int, int], dots_to_spawn: int = 4, empty_spaces: int = 1) -> None:
        self._board_size: tuple[int, int] = board_size
        self._total_spaces: int = board_size[0] * board_size[1]
        self._dots_to_spawn: int = dots_to_spawn
        self._empty_spaces: int = empty_spaces

        self._tiles: list[ActiveTile | EmptyTile] = []

        self._empty_tiles: list[EmptyTile] = [EmptyTile(self._total_spaces - i) for i in range(empty_spaces)]

        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def all_tiles(self) -> list[ActiveTile | EmptyTile]:
        """Return all tiles."""
        return self._tiles + self._empty_tiles

    def _make_tiles(self) -> None:
        """Make the tiles."""
        total_num = (self._total_spaces - self._empty_spaces) * (self._dots_to_spawn // 2)
        paired_num = list(range(total_num)) * 2
        random.shuffle(paired_num)
        for i in range(self._total_spaces):
            if i < self._empty_spaces:
                self._tiles.append(self._empty_tiles[i])
            else:
                dot_numbers = random.sample(paired_num, self._dots_to_spawn)
                self._tiles.append(ActiveTile(i, dot_numbers))

                for num in dot_numbers:
                    paired_num.remove(num)

    def make_board(self) -> None:
        """Make the board."""
        print(self._board_size)
        """number_filled_tiles = self.board_size**2-self.empty_tiles
        total_numbers = number_filled_tiles*self.tile_size
        all_numbers = list(range(total_numbers//2))*2

        while True:
            random.shuffle(all_numbers)
            grouped_numbers = [*batched(all_numbers, self.tile_size)]
            if all(map(lambda a: len(a) == len(set(a)), grouped_numbers)):
                break

        for i, j in enumerate(random.sample(range(self.board_size**2), number_filled_tiles)):
            self.tile_dict[j] = ActiveTile(tuple(grouped_numbers[i]))
            """


class GameFlow:
    """Game Flow class."""

    def __init__(self) -> None:
        self._players: list[Player] = []

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
