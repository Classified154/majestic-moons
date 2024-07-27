import asyncio
import random
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from pathlib import Path

import disnake
from disnake.ext import commands
from PIL import Image, ImageDraw, ImageFont

TICK = "✅"
CROSS = "❌"
TIME_REMEMBER = 10  # Seconds


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
        super().__init__("Empty Tile doesn't have dots")


class DotNotFoundError(Exception):
    """Tile Not Found Exception."""

    def __init__(self, index: int, tile_num: int) -> None:
        super().__init__(f"Dot {index} not found in Tile {tile_num}")


def select_unique_numbers(numbers: list[int], count: int) -> list[int]:
    """Select unique numbers."""
    selected = []
    random.shuffle(numbers)

    for num in numbers:
        if num not in selected:
            selected.append(num)
            if len(selected) == count:
                break

    while len(selected) < count:
        num = random.choice(numbers)  # noqa: S311
        if num not in selected:
            selected.append(num)

    return selected


class TileStatus(Enum):
    """Tile Status class."""

    EMPTY = 0
    FILLED = 1


class NumberStatus(Enum):
    """Number Status class."""

    VISIBLE = 0
    HIDDEN = 1


class GameDifficulty(Enum):
    """Game Difficulty class."""

    EASY = 3
    MEDIUM = 4
    HARD = 5


@dataclass
class Player:
    """Player class."""

    user: disnake.Member | None
    bot: bool = False
    turn: bool = False
    score: int = 0

    @property
    def user_id(self) -> int:
        """Return the user ID."""
        return self.user.id if self.user else None

    @property
    def username(self) -> str:
        """Return the username."""
        return self.user.name if self.user else None

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
        self._is_moved = False

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

    @property
    def is_moved(self) -> bool:
        """Return indexes of all adjacent tiles."""
        return self._is_moved

    @is_moved.setter
    def is_moved(self, value: bool) -> None:
        self._is_moved = value

    @property
    def dots_found(self) -> list[Dot]:
        """Show the dots that are found."""
        return [dot for dot in self._dots if dot.found]

    @property
    def dots_not_found(self) -> list[Dot]:
        """Show the dots that are not found."""
        return [dot for dot in self._dots if not dot.found]

    def set_dot_found(self, position: int) -> None:
        """Mark a dot as found."""
        self._dots[position].found = True


class Board:
    """Board class."""

    def __init__(
        self,
        msg_id: int,
        num_stones: GameDifficulty,
        players: list[Player],
        dots_to_spawn: int = 4,
        empty_spaces: int = 1,
    ) -> None:
        self._msg_id: int = msg_id
        self._num_stones: int = num_stones  # 3, 4, 5
        self._board_size: tuple[int, int] = (3, 3)
        self._total_spaces: int = 9  # 3 x 3
        self._dots_to_spawn: int = dots_to_spawn
        self._empty_spaces: int = empty_spaces
        self._user: Player = players[0]
        self._opponent: Player = players[-1]

        self._tiles: list[ActiveTile | EmptyTile] = []

        self._empty_tiles: list[EmptyTile] = []

        self._lock: asyncio.Lock = asyncio.Lock()
        self._user.turn = True
        self._opponent.turn = False
        self.padding: dict[str, int] = {
            "top": 15,
            "bottom": 30,
            "left": 45,
            "right": 20,
        }
        self.ROCK_SIZE: tuple[int, int] = (40, 40)
        self.font = ImageFont.truetype("../assets/arial.ttf", 18)

        # Load raft images
        self.raft_images = []
        for i in range(4):
            raft_path = f"../assets/raft/tile{i:03d}.png"
            if Path.exists(Path(raft_path)):
                raft_img = Image.open(raft_path).convert("RGBA")
                self.raft_images.append(raft_img)
        self.raft_width, self.raft_height = self.raft_images[0].size

        # Load rock images
        self.rock_images = []
        for i in range(1, 6):
            rock_path = f"../assets/rocks/tile{i:03d}.png"
            if Path.exists(Path(rock_path)):
                rock_img = Image.open(rock_path).convert("RGBA")
                rock_img = rock_img.resize(self.ROCK_SIZE, Image.Resampling.LANCZOS)
                self.rock_images.append(rock_img)

        self.raft_offset = 10
        self.board_width: int = (self._board_size[0] * self.raft_width) + ((self._board_size[0] - 1) * 10)
        self.board_height: int = (self._board_size[1] * self.raft_height) + ((self._board_size[1] - 1) * 10)

    def __iter__(self) -> iter:
        return iter(self.all_tiles)

    def __repr__(self) -> str:
        return f"Board(Message ID:{self._msg_id}, Size:{self._board_size}, Players:{self._user}, {self._opponent})"

    def __getitem__(self, index: int) -> ActiveTile | EmptyTile:
        for t in self.all_tiles:
            if t.num == index:
                return t

        raise TileNotFoundError(index)

    @property
    def num_stones(self) -> int:
        """Return the number of stones."""
        return self._num_stones

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
        return self._tiles

    @property
    def active_tiles(self) -> list[ActiveTile]:
        """Return all active tiles."""
        return [tile for tile in self.all_tiles if isinstance(tile, ActiveTile)]

    @property
    def all_players_id(self) -> list[int]:
        """Return all player IDs."""
        return [self._user.user_id, self._opponent.user_id]

    @property
    def current_player(self) -> Player:
        """Return the current player."""
        return self._user if self._user.turn else self._opponent

    def change_turn(self) -> None:
        """Switches the turn of players."""
        if self._user.turn:
            if not self._opponent.bot:
                self._user.turn = not self._user.turn
                self._opponent.turn = not self._opponent.turn
        else:
            self._user.turn = True
            self._opponent.turn = False

    def find_movable(self, tile: Tile) -> list[ActiveTile]:
        """Return the index of all adjacent tiles."""
        adjacent_tiles = []

        if tile.num % self._board_size[0] != 0:
            adj_tile = self.__getitem__(tile.num - 1)
            if not adj_tile.is_empty and not adj_tile.is_moved:
                adjacent_tiles.append(adj_tile)

        if tile.num % self._board_size[0] != self._board_size[0] - 1:
            adj_tile = self.__getitem__(tile.num + 1)
            if not adj_tile.is_empty and not adj_tile.is_moved:
                adjacent_tiles.append(adj_tile)

        if tile.num >= self._board_size[0]:
            adj_tile = self.__getitem__(tile.num - self._board_size[0])
            if not adj_tile.is_empty and not adj_tile.is_moved:
                adjacent_tiles.append(adj_tile)

        if tile.num < self._board_size[0] * (self._board_size[1] - 1):
            adj_tile = self.__getitem__(tile.num + self._board_size[0])
            if not adj_tile.is_empty and not adj_tile.is_moved:
                adjacent_tiles.append(adj_tile)

        return adjacent_tiles

    def _move_tiles(self) -> None:
        """Move the Empty tiles."""
        # We should move the empty itself to another position exchanging it with a filled tile
        moved_tiles = []
        for tile in self._empty_tiles:
            chosen_tile = random.choice(self.find_movable(tile))  # noqa: S311
            temp_tile = chosen_tile.num
            chosen_tile.num = tile.num
            tile.num = temp_tile
            chosen_tile.is_moved = True
            moved_tiles.append(chosen_tile.num)
            print()

        for tile in self.all_tiles:
            if not tile.is_empty:
                tile.is_moved = False
        for tile_num in moved_tiles:
            self[tile_num].is_moved = True

    def _get_dot_positions(self, num_dots: int, width: int, height: int) -> list[tuple[int, int]]:
        """Get the dot positions based on the number of dots to spawn."""
        if num_dots == 3:  # noqa: PLR2004
            positions = [
                (self.padding["left"], self.padding["top"]),
                (width - self.padding["right"] - self.ROCK_SIZE[0], self.padding["top"]),
                # Adding offset for the bottom stone (+15,0)
                (width // 2 - self.ROCK_SIZE[0] // 2 + 15, height - self.padding["bottom"] - self.ROCK_SIZE[1]),
            ]
        elif num_dots == 4:  # noqa: PLR2004
            positions = [
                (self.padding["left"], self.padding["top"]),
                (width - self.padding["right"] - self.ROCK_SIZE[0], self.padding["top"]),
                (self.padding["left"], height - self.padding["bottom"] - self.ROCK_SIZE[1]),
                (
                    width - self.padding["right"] - self.ROCK_SIZE[0],
                    height - self.padding["bottom"] - self.ROCK_SIZE[1],
                ),
            ]
        elif num_dots == 5:  # noqa: PLR2004
            positions = [
                (self.padding["left"], self.padding["top"]),
                (width - self.padding["right"] - self.ROCK_SIZE[0], self.padding["top"]),
                # Adding offset for the middle stone (+15, -2)
                (width // 2 - self.ROCK_SIZE[0] // 2 + 12, height // 2 - self.ROCK_SIZE[1] // 2 - 5),
                (self.padding["left"], height - self.padding["bottom"] - self.ROCK_SIZE[1]),
                (
                    width - self.padding["right"] - self.ROCK_SIZE[0],
                    height - self.padding["bottom"] - self.ROCK_SIZE[1],
                ),
            ]
        else:
            error_message = f"Expected 3, 4, or 5 dots, got {num_dots}"
            raise ValueError(error_message)

        return positions

    def _create_rock_with_number(self, number: str, numbers_visible: NumberStatus) -> Image.Image:
        """Create a rock image with or without the number visible on it."""
        if numbers_visible == NumberStatus.VISIBLE:
            rock = random.choice(self.rock_images).copy()  # noqa: S311
            draw = ImageDraw.Draw(rock)
            bbox = draw.textbbox((0, 0), number, font=self.font)
            text_width = bbox[2] - bbox[0] - 5
            text_height = bbox[3] - bbox[1] + 10
            position = ((self.ROCK_SIZE[0] - text_width) // 2, (self.ROCK_SIZE[1] - text_height) // 2)
            draw.text(position, number, fill=(0, 0, 0), font=self.font)
        else:
            rock = random.choice(self.rock_images).copy()  # noqa: S311
        return rock

    def _create_board_frame(self, raft_image: Image.Image, numbers_visible: NumberStatus) -> Image.Image:
        """Create a frame of the board for the GIF."""
        base = Image.new("RGB", (self.board_width, self.board_height), (135, 206, 235))
        draw = ImageDraw.Draw(base)

        for index, tile in enumerate(self.all_tiles):
            row = index // self._board_size[0]
            col = index % self._board_size[0]
            x = col * (self.raft_width + self.raft_offset)
            y = row * (self.raft_height + self.raft_offset)

            if isinstance(tile, EmptyTile):
                draw.rectangle([x, y, x + self.raft_width, y + self.raft_height], fill=(135, 206, 235))
            elif isinstance(tile, ActiveTile):
                base.paste(raft_image, (x, y), raft_image)
                numbers = [str(dot.num) for dot in tile]
                positions = self._get_dot_positions(self._num_stones, self.raft_width, self.raft_height)

                for num, pos, dot in zip(numbers, positions, tile, strict=False):
                    if not dot.found:
                        rock_with_number = self._create_rock_with_number(num, numbers_visible)
                        rock_x = x + pos[0]
                        rock_y = y + pos[1]
                        base.paste(rock_with_number, (rock_x, rock_y), rock_with_number)
                    else:
                        transparent_square = Image.new("RGBA", self.ROCK_SIZE, (0, 0, 0, 0))
                        square_x = x + pos[0]
                        square_y = y + pos[1]
                        base.paste(transparent_square, (square_x, square_y), transparent_square)

        return base

    def _generate_board_img(self, numbers_visible: NumberStatus) -> disnake.File:
        """Generate the board image as an animated GIF."""
        print("Generating board image")
        try:
            print(f"Board size: {self._board_size}")
            print(f"Number of tiles: {len(self._tiles)}")
            print(f"Number of active tiles: {sum(1 for tile in self._tiles if isinstance(tile, ActiveTile))}")
            frames = [self._create_board_frame(raft_image, numbers_visible) for raft_image in self.raft_images]

            buffer = BytesIO()
            frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:], duration=400, loop=0)
            buffer.seek(0)

            return disnake.File(fp=buffer, filename="board.gif")
        except Exception as e:  # noqa: BLE001
            print(f"An error occurred while generating the board image: {e!s}")

    def _make_tiles(self) -> None:
        total_num = ((self._total_spaces - self._empty_spaces) * self._num_stones) // 2
        paired_num = list(range(total_num)) * 2
        random.shuffle(paired_num)

        for i in range(self._total_spaces):
            if i > (self._total_spaces - self._empty_spaces - 1):
                empty_tile = EmptyTile(i)
                self._tiles.append(empty_tile)
                self._empty_tiles.append(empty_tile)
                print(f"Empty tile {i} added")
            else:
                dot_numbers = select_unique_numbers(paired_num, self._num_stones)
                self._tiles.append(ActiveTile(i, dot_numbers))

                for num in dot_numbers:
                    paired_num.remove(num)

                print(f"Active tile {i} added")

    def make_board(self) -> disnake.File:
        """Make the board."""
        self._make_tiles()
        return self._generate_board_img(NumberStatus.VISIBLE)
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
        num_stones: GameDifficulty,
        user: disnake.Member,
        opponent: disnake.Member | None,
        dots_to_spawn: int = 4,
        empty_spaces: int = 1,
    ) -> tuple[Board, disnake.File]:
        """Create a board."""
        _is_opponent_bot = opponent is None

        board = Board(
            msg_id,
            num_stones,
            [Player(user=user, bot=False), Player(user=opponent, bot=_is_opponent_bot)],
            dots_to_spawn,
            empty_spaces,
        )
        board_img = board.make_board()
        self._boards.append(board)
        return board, board_img

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


class TurnDropdown(disnake.ui.StringSelect):
    """A dropdown that lets user choose from tile and dot coordinates."""

    def __init__(self, label: str, board: Board, dot_list: list[Dot] | None = None) -> None:
        self.label = label
        self.board = board
        lst_to_iter: list = board.active_tiles if label == "Tile" else dot_list
        options = [
            *(
                disnake.SelectOption(label=f"{_index + 1}", value=f"{_index + 1}")
                for _index in range(len(lst_to_iter))
            ),
        ]

        super().__init__(
            placeholder=f"Choose a {label}",
            max_values=1,
            options=options,
            custom_id=f"{label.lower()}_dropdown",
        )

    async def callback(self, inter: disnake.MessageInteraction) -> None:
        """Dropdown callback."""
        _cords = int(inter.resolved_values[0]) - 1

        if self.label == "Tile":
            for i, _c in enumerate(self.view.children):
                if i > 0:
                    self.view.remove_item(_c)
            self.view.tile_cords = _cords
            self.view.add_item(TurnDropdown("Dot", self.board, self.board[self.view.tile_cords].dots_not_found))
            await inter.response.edit_message(view=self.view)
        else:
            self.view.dot_cords = _cords
            await self.view.finish_view(inter)


class TurnView(disnake.ui.View):
    """A view that contain dropdown."""

    def __init__(self, board: Board, msg_id: int) -> None:
        super().__init__(timeout=None)
        self.tile_cords = 0
        self.dot_cords = 0
        self.board = board
        self.msg_id = msg_id
        self.add_item(TurnDropdown("Tile", board))

    async def finish_view(self, inter: disnake.MessageInteraction) -> None:
        """Finish the view."""
        self.clear_items()
        self.stop()
        # Process inputs here
        await inter.response.send_message(
            f"Tile coordinates: {self.tile_cords}, Dot coordinates: {self.dot_cords}, "
            f"Dot you selected is {game_flow[self.msg_id][int(self.tile_cords)][int(self.dot_cords)]}",
            ephemeral=True,
            view=self,
        )
        # Update the board
        # Check if the game is over
        # Change the turn
        self.board.change_turn()


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

        view = TurnView(board, msg_id=inter.message.id)
        self.play_turn.disabled = True
        await inter.message.edit(view=self)
        await inter.response.send_message(view=view, ephemeral=True)

        await view.wait()

        self.play_turn.disabled = False
        await inter.message.edit(view=self)


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
    async def game(self, inter: disnake.MessageCommandInteraction, difficulty: GameDifficulty) -> None:  # noqa: D417
        """Start a game against the computer.

        Parameters
        ----------
        difficulty: Choose game difficulty.

        """
        await inter.response.defer()
        msg = await inter.original_message()

        board, board_img = game_flow.create_board(
            msg_id=msg.id,
            num_stones=difficulty,
            user=inter.author,
            opponent=None,
        )
        await inter.edit_original_message(f"This is your board. Look carefully \n\nDebug:{board}")

        message = await inter.channel.send(file=board_img)
        await asyncio.sleep(TIME_REMEMBER)
        await message.delete()
        view = MainView()
        await inter.edit_original_message("Click the button to play your turn.", view=view)

    @commands.slash_command(name="game-vs")
    @commands.default_member_permissions(administrator=True)
    async def game_vs(  # noqa: D417
        self, inter: disnake.CommandInteraction, opponent: disnake.Member, difficulty: GameDifficulty
    ) -> None:
        """Start your game.

        Parameters
        ----------
        inter: The interaction.
        opponent: Mention a user you want to play with.
        difficulty: Choose game difficulty.

        """
        await inter.response.defer()
        msg = await inter.original_message()

        board, board_img = game_flow.create_board(
            msg_id=msg.id,
            num_stones=difficulty,
            user=inter.author,
            opponent=opponent,
        )

        await inter.edit_original_message(f"This is your board. Look carefully\n\nDebug:{board}", view=MainView())
        message = await inter.channel.send(file=board_img)
        await message.delete(delay=TIME_REMEMBER)


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
