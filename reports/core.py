import logging
from typing import Optional

import discord
from redbot.core import Config, checks, commands

BASECOG = getattr(commands, "Cog", object)
DEF_GUILD = {
    "report_channel": None,
    "emote_reactions": False,
    "claim_reports": False,
    "recieve_dms": [],
}

# TODO Add reportdm command to disable dms on reports. To avoid annoyed members.


class Reports(BASECOG):
    """
    Berichtssystem
    Mitglieder können `[p]report <Benutzer> <Grund>` eingeben und es wird in deinem ausgewählten Kanal angezeigt!
    """

    __author__ = ["Jelly"]
    __version__ = "1.1.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=2233914253021)
        self.config.register_guild(**DEF_GUILD)

        self.log = logging.getLogger("red.cogs.reports")

    async def red_delete_data_for_user(self, **kwargs):
        """
        Nothing to delete
        """
        return

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        authors = ", ".join(self.__author__)
        return f"{context}\n\nAuthor: {authors}\nVersion: {self.__version__}"

    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.user)
    @commands.command(usage="")
    async def reportdm(self, ctx):
        """
        Aktiviert/deaktiviert die Nachrichten, die der Bot bei einer Meldung sendet.
        Standardmäßig ändert sich dies je nach Ihrer aktuellen Einstellung.
        """
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

        status = None
        async with self.config.guild(ctx.guild).recieve_dms() as dmreport:
            if ctx.author.id not in dmreport:
                dmreport.append(ctx.author.id)
                status = True
            else:
                dmreport.remove(ctx.author.id)
                status = False

        message = "Erledigt. Du wirst {status} DMs erhalten, wenn du meldest".format(
            status="not" if status else "now"
        )

        try:
            await ctx.author.send(message)
        except discord.HTTPException:
            await ctx.send(message)

    @commands.guild_only()
    @commands.cooldown(2, 15, commands.BucketType.user)
    @commands.command(usage="<member> <reason>")
    async def report(self, ctx, member: Optional[discord.Member], *, reason: str):
        """
        Ein Mitglied melden
        Beispiel: !report @DiscordUser#0001 Ist nicht fischig genug.
        Argumente:
        `Mitglied`: Das Discord-Mitglied, das du melden willst
        `Grund`: Der Grund für die Meldung
        """
        report_channel = await self.config.guild(ctx.guild).report_channel()
        if report_channel is None:
            try:
                return await ctx.author.send(
                    "Es tut uns leid! Das Moderationsteam auf diesem Server hat noch keinen Bericht erstellt "
                    "Kanal noch nicht. Bitte wende dich an das Moderationsteam und frage, ob sie "
                    "Stell einen auf!"
                )
            except (discord.Forbidden, discord.NotFound):
                pass

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            self.log.info("Unable to delete message in {}".format(ctx.channel.name))

        await self.build_report_embeds(ctx, member, reason, report_channel)

    async def build_report_embeds(self, ctx, member, reason, report_channel):
        """
        Baut Einbettungen für den Bericht
        Wenn Mitglied Keine ist. Standardmäßig kein Benutzer
        """
        embed = discord.Embed()
        embed.description = "**Grund**:\n{}".format(reason)
        embed.timestamp = ctx.message.created_at

        if member is None:
            embed.add_field(name="User", value="Kein Benutzer erkannt.")
        else:
            embed.add_field(name="User", value="{}\n**ID**: {}".format(member.mention, member.id))

        if member is None or member.voice is None:
            embed.add_field(name="Channel", value=ctx.channel.mention)
        else:
            embed.add_field(
                name="Channel",
                value="{}\n**VC**: {}".format(ctx.channel.mention, member.voice.channel.mention),
            )

        if ctx.author is None:
            embed.add_field(name="Author", value="Kein Autor gefunden")
        else:
            embed.add_field(name="Author", value=ctx.author.mention)

        await self.send_report_to_mods(ctx, embed, report_channel)

    async def send_report_to_mods(self, ctx, embed, report_channel):
        """
        Sending to channel
        """
        channel_report = self.bot.get_channel(report_channel)
        try:
            await channel_report.send(embed=embed)
        except discord.Forbidden:
            self.log.warning("Unable to send message in {}".format(channel_report))
        except discord.HTTPException as e:
            self.log.warning("HTTPException {} - {}".format(e.code, e.status))

        if ctx.author.id in await self.config.guild(ctx.guild).recieve_dms():
            return

        try:
            await ctx.author.send(
                "Vielen Dank für deinen Bericht. Das Moderationsteam hat deinen Bericht erhalten."
            )
        except (discord.Forbidden, discord.HTTPException):
            self.log.info(
                "Nachricht kann nicht gesendet werden an {} - {}".format(ctx.author.name, ctx.author.id)
            )

    @report.error
    async def _report_error_handler(self, ctx, error):
        """Fehlerhandler für den Report-Befehl"""
        if isinstance(error, commands.CommandOnCooldown):
            try:
                await ctx.message.delete()
            except (discord.errors.Forbidden, discord.errors.HTTPException):
                pass
            try:
                return await ctx.author.send(
                    "Deine Meldung wurde auf einen bestimmten Satz begrenzt. Bitte keine Massenmeldung."
                )
            except (discord.errors.Forbidden, discord.errors.HTTPException):
                pass
        else:
            await ctx.bot.on_command_error(ctx, error, unhandled_by_cog=True)

    @checks.mod_or_permissions(kick_members=True)
    @commands.group()
    async def reportset(self, ctx):
        """
        Verwalte das Berichtssystem
        """
        pass

    @reportset.command(name="list")
    async def show_settings(self, ctx):
        """
        Zeigt die Berichtseinstellungen an
        """
        guild_config = await self.config.guild(ctx.guild).all()
        report_channel = guild_config["report_channel"]
        emotes_toggle = guild_config["emote_reactions"]
        claim_toggle = guild_config["claim_reports"]

        embed = discord.Embed()
        embed.title = "{}'s Report Settings".format(ctx.guild.name)
        embed.add_field(
            name="Report Channel",
            value="<#{}>".format(report_channel) if report_channel else "No channel set",
            inline=False,
        )
        embed.add_field(
            name="Auto Emote Reaction", value="enabled" if emotes_toggle else "disabled"
        )
        embed.add_field(name="Moderation Claim", value="enabled" if claim_toggle else "disabled")

        await ctx.send(embed=embed)

    @reportset.command(name="reportclaim")
    async def report_claim(self, ctx, toggle: Optional[bool]):
        """
        Bericht einschalten, um beansprucht zu werden.
        Wenn diese Option aktiviert ist, wird jede Reaktion auf einen Bericht sofort vom Moderator eingefordert..
        """
        report_toggle = self.config.guild(ctx.guild).claim_reports
        if toggle is None:
            return await ctx.send(
                "Bericht Anspruch sind {}".format("enabled" if await report_toggle() else "disabled")
            )
        elif toggle is True:
            await report_toggle.set(True)
            return await ctx.send("Die Einstellung ist jetzt aktiviert.")
        elif toggle is False:
            await report_toggle.set(False)
            return await ctx.send("Die Einstellung ist jetzt deaktiviert.")

    @reportset.command()
    async def channel(self, ctx, channel: Optional[discord.TextChannel]):
        """
        Legt den Kanal fest, in dem die Berichte gepostet werden
        """
        if channel is None:
            await self.config.guild(ctx.guild).report_channel.set(None)
            return await ctx.send("Erledigt. Lösche den Berichtskanal.")

        await self.config.guild(ctx.guild).report_channel.set(channel.id)
        await ctx.send("Erledigt. Lege {} als Berichtskanal fest.".format(channel.mention))

    @reportset.command()
    async def emotes(self, ctx, toggle: Optional[bool]):
        """
        Legt fest, ob der Bot automatisch Reaktionen für jeden gesendeten Bericht setzt
        Oben bestätigt, dass es sich um eine gültige Meldung handelt
        Unten bedeutet, dass es sich um eine ungültige Meldung handelt
        Frage bedeutet, dass du dir nicht sicher bist, ob die Meldung gültig ist oder ob du sie anzweifelst.
        X bedeutet, dass es zu lange her ist, um es zu überprüfen
        """
        emotes_toggle = self.config.guild(ctx.guild).emote_reactions
        if toggle is None:
            return await ctx.send(
                "Emotes are {}".format("enabled" if await emotes_toggle() else "disabled")
            )
        elif toggle is True:
            await self.config.guild(ctx.guild).emote_reactions.set(True)
            return await ctx.send("Die Einstellung ist jetzt aktiviert")
        elif toggle is False:
            await self.config.guild(ctx.guild).emote_reactions.set(False)
            return await ctx.send("Die Einstellung ist jetzt deaktiviert")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Automatisches Hinzufügen von Reaktionen
        """
        if not message.guild:
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        report_channel = await self.config.guild(message.guild).report_channel()

        if await self.config.guild(message.guild).emote_reactions() is False:
            return False

        if report_channel is None:
            return False

        if message.author == self.bot.user:
            emote_channel = discord.utils.get(message.guild.channels, id=int(report_channel))
            if message.channel != emote_channel:
                return False

            reaction_emotes = ["👋", "👍", "👎", "❓", "❌"]
            for emotes in reaction_emotes:
                try:
                    await message.add_reaction(emotes)
                except discord.NotFound:
                    return  # No need to log if message was removed
                except (discord.Forbidden, discord.HTTPException):
                    self.log.info("Unfähig zu reagieren in {}".format(emote_channel))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """
        Erkennt, wenn jemand eine Reaktion hinzufügt
        """
        if not reaction.message.guild:
            return

        if await self.bot.cog_disabled_in_guild(self, reaction.message.guild):
            return False

        if user.id == self.bot.user.id:
            return

        config_info = await self.config.guild(reaction.message.guild).all()
        if config_info["report_channel"] is None:
            return

        if config_info["claim_reports"] is False:
            return

        report_channel = discord.utils.get(
            reaction.message.guild.channels, id=int(config_info["report_channel"])
        )
        if reaction.message.channel != report_channel:
            return

        if (
            reaction.message.embeds
            and "Moderator Beansprucht:" in str(reaction.message.embeds[0].fields)
            or "hat dies behauptet." in reaction.message.content
            or not reaction.message.embeds
        ):
            return

        message = reaction.message
        if message.author.id != self.bot.user.id:
            return

        try:
            embed = message.embeds[0]
            embed.add_field(
                name="Moderator Claimed:", value="{} ({})".format(user.mention, user.id)
            )
            await message.edit(embed=embed)
        except IndexError:
            await message.edit("{} ({}) hat dies behauptet.".format(user.mention, user.id))

    # Reason for no try on editing is because we check if it's the bot's message before editing
