import asyncio
import random
from dataclasses import dataclass
from enum import Enum
from io import BytesIO

import disnake
from disnake.ext import commands
from PIL import Image

TICK = "✅"
CROSS = "❌"


class TileNotFoundError(Exception):
    """Tile Not Found Exception."""

    def __init__(self, index: int) -> None:
        super().__init__(f"No tile found matching the {index}")


class BoardNotFoundError(Exception):
    """Tile Not Found Exception."""

    def __init__(self, index: int) -> None:
        super().__init__(f"No board found matching the {index}")


class EmptyTileDotError(Exception):
    """Tile Not Found Exception."""

    def __init__(self) -> None:
        super().__init__("Empty Tile doesnt have dots")


class DotNotFoundError(Exception):
    """Tile Not Found Exception."""

    def __init__(self, index: int, tile_num: int) -> None:
        super().__init__(f"Dot {index} not found in Tile {tile_num}")


def select_unique_numbers(numbers: list[int], count: int) -> list[int]:
    """Select unique numbers."""
    unique_numbers = list(set(numbers))  # Get unique numbers
    return random.sample(unique_numbers, count)


class TileStatus(Enum):
    """Tile Status class."""

    EMPTY = 0
    FILLED = 1


@dataclass
class Player:
    """Player class."""

    user: disnake.Member
    turn: bool = False
    score: int = 0

    @property
    def user_id(self) -> int:
        """Return the user ID."""
        return self.user.id

    @property
    def username(self) -> str:
        """Return the username."""
        return self.user.name

    def __repr__(self) -> str:
        return f"Player(User ID:{self.user_id}, Username:{self.username}, Score:{self.score})"

    def __str__(self) -> str:
        return self.__repr__()


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

    @property
    def num(self) -> int:
        """Return the number."""
        return self._num

    @num.setter
    def num(self, value: int) -> None:
        self._num = value


class EmptyTile(Tile):
    """Empty Tile class."""

    def __init__(self, num: int) -> None:
        super().__init__(num, TileStatus.EMPTY)

    def __repr__(self) -> str:
        return f"EmptyTile(Number:{self._num}, Empty:True)"

    def __getitem__(self, index: int) -> None:
        raise EmptyTileDotError

    def __eq__(self, other: object) -> bool:
        return NotImplemented


class ActiveTile(Tile):
    """Tile class."""

    def __init__(self, num: int, dots_num: list[int]) -> None:
        super().__init__(num, TileStatus.FILLED)
        self._dots: list[Dot] = [Dot(i) for i in dots_num]

    def __repr__(self) -> str:
        return f"ActiveTile((Number:{self._num}, Dots:{self._dots}, Empty:False)"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ActiveTile):
            return any(self_dot.num == other_dot.num for self_dot in self._dots for other_dot in other)

        return NotImplemented

    def __iter__(self) -> iter:
        return iter(self._dots)

    def __getitem__(self, index: int) -> Dot:
        if 0 <= index < len(self._dots):
            return self._dots[index]

        raise DotNotFoundError(index, self._num)

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

    def __init__(
        self,
        msg_id: int,
        board_size: tuple[int, int],
        players: list[Player],
        dots_to_spawn: int = 4,
        empty_spaces: int = 1,
    ) -> None:
        self._msg_id: int = msg_id
        self._board_size: tuple[int, int] = board_size
        self._total_spaces: int = board_size[0] * board_size[1]
        self._dots_to_spawn: int = dots_to_spawn
        self._empty_spaces: int = empty_spaces
        self._user: Player = players[0]
        self._opponent: Player = players[1]

        self._tiles: list[ActiveTile | EmptyTile] = []

        self._empty_tiles: list[EmptyTile] = [EmptyTile(self._total_spaces - i) for i in range(empty_spaces)]

        self._lock: asyncio.Lock = asyncio.Lock()

    def __iter__(self) -> iter:
        return iter(self.all_tiles)

    def __getitem__(self, index: int) -> ActiveTile | EmptyTile:
        for t in self.all_tiles:
            if t.num == index:
                return t

        raise TileNotFoundError(index)

    @property
    def msg_id(self) -> int:
        """Return the message id."""
        return self._msg_id

    @property
    def lock(self) -> asyncio.Lock:
        """Return the lock."""
        return self._lock

    @property
    def all_tiles(self) -> list[ActiveTile | EmptyTile]:
        """Return all tiles."""
        return self._tiles + self._empty_tiles

    @property
    def all_players_id(self) -> list[int]:
        """Return all player IDs."""
        return [self._user.user_id, self._opponent.user_id]

    @property
    def current_player(self) -> Player:
        """Return the current player."""
        return self._user if self._user.turn else self._opponent

    def _change_turn(self) -> None:
        if self._user.turn:
            self._user.turn = False
            self._opponent.turn = True
        else:
            self._user.turn = True
            self._opponent.turn = False

    def _move_tiles(self) -> None:
        """Move the Empty tiles."""

    # We should move the empty itself to another position exchanging it with a filled tile

    def _generate_board_img(self) -> disnake.File:
        """Generate the board image."""
        base: Image = Image.new("RGB", (self._board_size[0] * 100, self._board_size[1] * 100), (255, 255, 255))

        # Create stuff here

        buffer = BytesIO()
        base.save(buffer, "png")
        buffer.seek(0)

        return disnake.File(fp=buffer, filename="board.png")

    def _make_tiles(self) -> None:
        total_num = (self._total_spaces - self._empty_spaces) * (self._dots_to_spawn // 2)
        paired_num = list(range(total_num)) * 2
        random.shuffle(paired_num)
        for i in range(self._total_spaces):
            if i < self._empty_spaces:
                self._tiles.append(self._empty_tiles[i])
            else:
                dot_numbers = select_unique_numbers(paired_num, self._dots_to_spawn)
                self._tiles.append(ActiveTile(i, dot_numbers))

                for num in dot_numbers:
                    paired_num.remove(num)

    def make_board(self) -> None:
        """Make the board."""
        print(self._board_size)

    # Need to make tiles
    # generate board image
    # setup cords


class GameFlow:
    """Game Flow class."""

    def __init__(self) -> None:
        self._boards: list[Board] = []
        self._players: list[Player] = []

    def __getitem__(self, msg_id: int) -> Board:
        """Retrieve a board by its message ID."""
        for board in self._boards:
            if board.msg_id == msg_id:
                return board

        raise BoardNotFoundError(msg_id)

    @property
    def player_one(self) -> Player:
        """Return Player 1."""
        return self._players[0]

    @property
    def player_two(self) -> Player:
        """Return Player 2."""
        return self._players[1]

    @property
    def boards(self) -> list[Board]:
        """Return the boards."""
        return self._boards

    def create_board(
        self,
        msg_id: int,
        board_size: tuple[int, int],
        user: disnake.Member,
        opponent: disnake.Member,
        dots_to_spawn: int = 4,
        empty_spaces: int = 1,
    ) -> None:
        """Create a board."""
        board = Board(msg_id, board_size, [Player(user=user), Player(user=opponent)], dots_to_spawn, empty_spaces)
        board.make_board()
        self._boards.append(board)

    def get_dot_by_cords(self, msg_id: int, tile_num: int, dot_num: int) -> Dot:
        """Find a dot."""
        for board in self._boards:
            if board.msg_id == msg_id:
                tile = board[tile_num]
                return tile[dot_num]

        raise BoardNotFoundError(msg_id)

    def get_tile_by_cords(self, msg_id: int, tile_num: int) -> ActiveTile | EmptyTile:
        """Find a tile."""
        for board in self._boards:
            if board.msg_id == msg_id:
                return board[tile_num]

        raise BoardNotFoundError(msg_id)


game_flow: GameFlow = GameFlow()


class TurnModal(disnake.ui.Modal):
    """A modal that prompts the user to enter the tile and dot coordinates for their turn."""

    def __init__(self) -> None:
        components = [
            disnake.ui.TextInput(
                label="Tile Coordinates",
                custom_id="tile_cords",
                style=disnake.TextInputStyle.short,
                placeholder="Enter the tile coordinates (e.g., 1,2)",
                min_length=3,
                max_length=5,
            ),
            disnake.ui.TextInput(
                label="Dot Coordinates",
                custom_id="dot_cords",
                style=disnake.TextInputStyle.short,
                placeholder="Enter the dot number (e.g., 1)",
                min_length=1,
                max_length=2,
            ),
        ]
        super().__init__(title="Your Turn", custom_id="turn_modal", components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        """Modal Callback."""
        tile_cords = inter.text_values["tile_cords"]
        dot_cords = inter.text_values["dot_cords"]
        # Process inputs here
        await inter.response.send_message(
            f"Tile coordinates: {tile_cords}, Dot coordinates: {dot_cords}",
            ephemeral=True,
        )


class MainView(disnake.ui.View):
    """Main View class."""

    def __init__(self) -> None:
        super().__init__(timeout=None)

    @disnake.ui.button(label="Play Turn", style=disnake.ButtonStyle.green, custom_id="play_your_turn")
    async def play_turn(self, _: disnake.Button, inter: disnake.MessageInteraction) -> None:
        """Button to play your turn."""
        board = game_flow[inter.message.id]
        if inter.author.id not in board.all_players_id:
            await inter.response.send_message("You are not in the game!", ephemeral=True)
            return

        player = board.current_player
        if player.user_id != inter.author.id:
            await inter.response.send_message("Please wait for your turn!", ephemeral=True)
            return

        modal = TurnModal()
        await inter.response.send_modal(modal)


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
