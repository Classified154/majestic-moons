import disnake
import os
import aiosqlite
from disnake.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

INTENTS = disnake.Intents.default()
INTENTS.members = True
INTENTS.message_content = True


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = "main.sqlite"
        self.cog_path = "./cogs"

    async def commit(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.commit()

    async def execute(self, query, *values):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                await cur.execute(query, tuple(values))
            await db.commit()

    async def executemany(self, query, values):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                await cur.executemany(query, values)
            await db.commit()

    async def fetchval(self, query, *values):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                exe = await cur.execute(query, tuple(values))
                val = await exe.fetchone()
            return val[0] if val else None

    async def fetchrow(self, query, *values):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                exe = await cur.execute(query, tuple(values))
                row = await exe.fetchmany(size=1)
            if len(row) > 0:
                row = [r for r in row[0]]
            else:
                row = None
            return row

    async def fetchmany(self, query, size, *values):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                exe = await cur.execute(query, tuple(values))
                many = await exe.fetchmany(size)
            return many

    async def fetch(self, query, *values):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cur:
                exe = await cur.execute(query, tuple(values))
                all_rows = await exe.fetchall()
            return all_rows


bot = MyBot(command_prefix="!",
            intents=INTENTS,
            test_guilds=[1263028897256312872],
            help_command=None,
            )


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})\n------")


@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension):
    """Reload an extension"""
    bot.reload_extension(f"cogs.{extension}")
    await ctx.send(embed=disnake.Embed(
        description=f"`{extension.upper()}` reloaded!",
        color=disnake.Color.dark_gold()))


@bot.command()
@commands.has_permissions(administrator=True)
async def load(ctx, extension):
    """Load an extension"""
    bot.load_extension(f"cogs.{extension}")
    await ctx.send(embed=disnake.Embed(
        description=f"`{extension.upper()}` loaded!",
        color=disnake.Color.dark_gold()))


for file in os.listdir(bot.cog_path):
    if file.startswith("!"):
        pass
    elif file.endswith(".py"):
        bot.load_extension(f"cogs.{file[:-3]}")


bot.run(TOKEN)
