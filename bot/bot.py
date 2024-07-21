import os

import aiosqlite
import disnake
from disnake.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

INTENTS = disnake.Intents.default()
INTENTS.members = True
INTENTS.message_content = True


class MyBot(commands.Bot):
    """Custom Bot class."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.db_path = "main.sqlite"
        self.cog_path = "./cogs"

    async def commit(self) -> None:
        """Commit the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.commit()

    async def execute(self, query: str, *values: object) -> None:
        """Execute a query."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                await cur.execute(query, tuple(values))
            await db.commit()

    async def executemany(self, query: str, values: tuple) -> None:
        """Execute many queries."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                await cur.executemany(query, values)
            await db.commit()

    async def fetchval(self, query: str, *values: str) -> str:
        """Fetch a single value."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                exe = await cur.execute(query, tuple(values))
                val = await exe.fetchone()
            return val[0] if val else None

    async def fetchrow(self, query: str, *values: object) -> list:
        """Fetch a single row."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                exe = await cur.execute(query, tuple(values))
                row = await exe.fetchmany(size=1)
            row: list = list(row[0]) if len(row) > 0 else None
            return row

    async def fetchmany(self, query: str, size: int, *values: object) -> list:
        """Fetch many rows."""
        async with aiosqlite.connect(self.db_path) as db, db.cursor() as cur:
            exe = await cur.execute(query, tuple(values))
            return await exe.fetchmany(size)

    async def fetch(self, query: str, *values: object) -> list:
        """Fetch all rows."""
        async with aiosqlite.connect(self.db_path) as db, db.cursor() as cur:
            exe = await cur.execute(query, tuple(values))
            return await exe.fetchall()


bot = MyBot(
    command_prefix="!",
    intents=INTENTS,
    test_guilds=[1263028897256312872],
    help_command=None,
)


@bot.event
async def on_ready() -> None:
    """Bot is ready."""
    print(f"Logged in as {bot.user} (ID: {bot.user.id})\n------")


@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx: commands.Context, extension: str) -> None:
    """Reload an extension."""
    bot.reload_extension(f"cogs.{extension}")
    await ctx.send(
        embed=disnake.Embed(description=f"`{extension.upper()}` reloaded!", color=disnake.Color.dark_gold()),
    )


@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx: commands.Context, extension: str) -> None:
    """Load an extension."""
    bot.load_extension(f"cogs.{extension}")
    await ctx.send(embed=disnake.Embed(description=f"`{extension.upper()}` loaded!", color=disnake.Color.dark_gold()))


for file in os.listdir(bot.cog_path):
    if file.startswith("!"):
        pass
    elif file.endswith(".py"):
        bot.load_extension(f"cogs.{file[:-3]}")

bot.run(TOKEN)
