import traceback
from time import time

import disnake
from disnake.ext import commands

C_Help = 0xFB3E8F
C_CommandHelp = 0xD70055
C_Nothing = 0xF05454
C_Error = 0xCC0B0B


class Help(commands.Cog):
    """Help command and error handler."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.CommandInteraction, error: commands.CommandError) -> None:
        """Error handler for slash commands."""
        if isinstance(error, commands.CommandOnCooldown):
            try:
                await inter.response.defer(ephemeral=True)
            except disnake.NotFound:
                return

            e_time = round(error.retry_after, 1)
            content = f"Command under cooldown, try again after <t:{int(time() + e_time)}:R>"

            await inter.edit_original_message(content=content)

        elif isinstance(error, commands.MissingPermissions):
            try:
                await inter.response.defer(ephemeral=True)
            except disnake.NotFound:
                return

            await inter.edit_original_message(content="The command is locked")

        elif isinstance(error, commands.CheckFailure):
            try:
                await inter.response.defer(ephemeral=True)
            except disnake.NotFound:
                return

            await inter.edit_original_message(content="❕ You can **not** do that here.")

        else:
            er_guild = self.bot.get_guild(1263028897256312872)
            er_channel = er_guild.get_channel(1264151369078800474)

            etype = type(error)
            trace = error.__traceback__

            lines = traceback.format_exception(etype, error, trace)
            traceback_text = "".join(lines)

            embed = disnake.Embed(
                title="Error",
                description=f"Author : {inter.author.mention} \n\n Command : `/{inter.data.name}` "
                f"\n\n```Python\n{traceback_text[:3500]}```",
                color=disnake.Color(C_Nothing),
            )
            await er_channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    """Add the cog to the bot."""
    bot.add_cog(Help(bot))
    print("[Help] Loaded")
