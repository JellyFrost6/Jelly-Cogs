import logging

import discord
from redbot.core import Config, checks, commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import humanize_list, pagify


class Verify(commands.Cog):
    """
    Überprüfungsprozess für Mitglieder
    Einrichtung eines Verifizierungsprozesses, bei dem die Mitglieder bestätigen müssen, dass sie die Regeln gelesen haben oder akzeptieren
    """

    __author__ = ["Efedc", "X"]
    __version__ = "1.0.1"

    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.log = logging.getLogger("red.cogs.verify")
        self.config = Config.get_conf(self, identifier=123532432623423)
        def_guild = {"toggle": False, "temprole": None, "logs": None, "autoroles": []}
        self.config.register_guild(**def_guild)
        self.config.register_global(version=None)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        authors = ", ".join(self.__author__)
        return f"{context}\n\nAuthors: {authors}\nVersion: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """
        Nothing to delete
        """
        return

    # Settings command, and output the settings.

    @commands.bot_has_permissions(
        manage_messages=True, send_messages=True, manage_roles=True, embed_links=True
    )
    @checks.mod_or_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.group()
    async def verifyset(self, ctx: commands.Context):
        """
        Verwaltet die Einstellungen für die Gilde.
        """
        if ctx.invoked_subcommand is None:
            guild = ctx.guild
            data = await self.config.guild(guild).all()
            color = await ctx.embed_color()
            role_config = data["temprole"], data["autoroles"]
            logs, toggle = data["logs"], data["toggle"]
            temprole = "Keine temporäre Rolle eingestellt, verwenden Sie `[p]verifyset temprole`, um eine zu verwenden."
            autoroles = "Siehe `{prefix}verifyset autorole list` für eine Liste der angegebenen Rollen.".format(
                prefix=ctx.prefix
            )
            if role_config[0]:
                temprole = discord.utils.get(ctx.guild.roles, id=role_config[0])

            if logs is None:
                log_info = (
                    "Es wurde kein Kanal für die Protokollierung festgelegt, verwende `{prefix}verifyset log`"
                    "erste.".format(prefix=ctx.prefix)
                )
            else:
                log_info = discord.utils.get(ctx.guild.text_channels, id=int(logs))

            embed = discord.Embed(color=color)
            embed.title = "{}'s Settings".format(guild.name)
            embed.description = (
                "Bitte stelle sicher, dass du den Verifizierungskanal und die ausgewählte Rolle eingerichtet hast.\nOnce "
                "Wenn das erledigt ist, musst du Active auf True setzen, sonst funktioniert es nicht."
            )
            embed.add_field(name="Aktiv:", value=toggle, inline=False)
            embed.add_field(name="Temporäre Rolle:", value=temprole, inline=True)
            embed.add_field(name="Rolle, die nach der Überprüfung zu geben ist:", value=autoroles, inline=True)
            embed.add_field(name="Logging-Kanal:", value=log_info, inline=True)
            await ctx.send(embed=embed)

    # If verification must be activated.

    @verifyset.command()
    async def active(self, ctx: commands.Context, toggle: bool = None):
        """
        Aktiviert oder deaktiviert den Verifizierungsprozess.
        Die Voreinstellung ist `False`, zum Aktivieren tippe `[p]verifyset activate True`.
        """
        guild = ctx.guild
        tog = self.config.guild(guild)
        role_config = [
            await tog.temprole(),
            await tog.autoroles(),
        ]
        if not role_config[1]:
            role_config[1] = None
        if toggle is None:
            message = "Die Einstellungen für die Verifizierung sind eingestellt auf {}.".format(await tog.toggle())
            if role_config.count(None) == 2 and await tog.toggle():
                await tog.toggle.set(False)
                message = (
                    "Ich habe die Verifizierung deaktiviert, da die Rollenanweisungen "
                    "entfernt. Prüfe die Einstellungen für weitere Informationen"
                )
            return await ctx.send(message)

        if role_config.count(None) == 2:
            return await ctx.send(
                "Mir fehlen Informationen; ich weiß nicht, ob ich eine vorläufige Antwort geben soll oder nicht. "
                "Rolle während der Verifizierung oder gib eine Rolle nach der Verifizierung."
            )
        await tog.toggle.set(toggle)
        await ctx.send("Die Überprüfungseinstellungen sind jetzt auf {choice}.".format(choice=toggle))

    # Channel used for logs.

    @verifyset.command()
    async def log(self, ctx: commands.Context, *, channel: discord.TextChannel = None):
        """
        Legt den Kanal fest, in den du loggen möchtest.
        Dies wird jedes Mal protokolliert, wenn jemand die Verifizierung akzeptiert.
        """
        guild = ctx.guild
        log_config = self.config.guild(guild)
        if channel is None:
            await log_config.logs.clear()
            return await ctx.send("Der Bot wird keine Aktionen mehr protokollieren, die.")

        await log_config.logs.set(channel.id)
        await ctx.send("Der Logging-Kanal ist jetzt eingestellt auf {}.".format(channel.mention))

    # Temporary role, which is given after joining and removed after verification.

    @verifyset.command()
    async def temprole(self, ctx: commands.Context, *, role: discord.Role = None):
        """
        Legt fest, welche Rolle den Benutzern zugewiesen wird, wenn sie der Gilde beitreten.
        Bitte stelle sicher, dass du die Rolle richtig einstellst, damit sie nur auf deine Regeln und/oder den
        Verifizierungskanal.
        """
        guild = ctx.guild
        role_config = self.config.guild(guild)
        role_set = await role_config.temprole()
        if role is None and role_set:
            await role_config.temprole.clear()
            return await ctx.send("Die verwendete Rolle gelöscht.")
        if role:
            if role >= ctx.author.top_role:
                return await ctx.send("Du kannst keine Rolle festlegen, die gleich oder höher ist als deine eigene.")

            if role >= ctx.guild.me.top_role:
                return await ctx.send(
                    "Du kannst keine Rolle festlegen, die gleich oder höher ist als die des Bot."
                )
            await role_config.temprole.set(role.id)
            await ctx.send(
                "Set the role to {}.".format(role.mention),
                allowed_mentions=discord.AllowedMentions(roles=False),
            )
        else:
            await ctx.send_help()

    # Autorole commands

    @verifyset.group()
    async def autorole(self, ctx: commands.Context):
        """
        Definiere Rollen, die vergeben werden, wenn ein Benutzer die Überprüfung besteht.
        """

    @autorole.command(name="add")
    async def add_roles(self, ctx: commands.Context, *roles: discord.Role):
        """Füge eine Rolle zum Geben hinzu.
        Du kannst mehr als eine Rolle zum Hinzufügen geben.
        """
        if not roles:
            return await ctx.send_help()
        errored = ""
        message = ""
        added = []
        already_added = []
        for role in roles:
            if role >= ctx.author.top_role:
                errored += (
                    "{role}: Du kannst keine Rolle festlegen, die gleich oder höher ist als deine eigene.\n".format(
                        role=role.name
                    )
                )
                continue
            if role >= ctx.guild.me.top_role:
                errored += (
                    "{role}: Du kannst keine Rolle festlegen, die gleich oder höher ist als der "
                    "bot.\n".format(role=role.name)
                )
                continue
            async with self.config.guild(ctx.guild).autoroles() as roles_list:
                if role.id not in roles_list:
                    roles_list.append(role.id)
                    added.append(role.name)
                else:
                    already_added.append(role.name)
        message += errored
        if added:
            message += "\nHinzugefügte Rolle(n): {roles}".format(roles=humanize_list(added))
        if already_added:
            message += "\nBereits hinzugefügte Rolle(n): {roles}".format(
                roles=humanize_list(already_added)
            )
        if message:
            for line in pagify(message):
                await ctx.send(line)

    @autorole.command(name="remove")
    async def remove_roles(self, ctx: commands.Context, *roles: discord.Role):
        """Entferne eine Rolle zum Geben.
        Du kannst mehr als eine Rolle zum Hinzufügen geben.
        """
        if not roles:
            return await ctx.send_help()
        message = ""
        removed = []
        not_found = []
        async with self.config.guild(ctx.guild).autoroles() as roles_list:
            for role in roles:
                if role.id in roles_list:
                    roles_list.remove(role.id)
                    removed.append(role.name)
                else:
                    not_found.append(role.name)
        if not_found:
            message += "\nRolle(n) nicht in der Autorollenliste gefunden: {roles}".format(
                roles=humanize_list(not_found)
            )
        if removed:
            message += "\nRolle(n) aus der Autorollenliste entfernen: {roles}".format(
                roles=humanize_list(removed)
            )
        if message:
            for line in pagify(message):
                await ctx.send(line)

    @autorole.command(name="list")
    async def list_roles(self, ctx: commands.Context):
        """Liste alle Rollen auf, die vergeben werden."""
        all_roles = await self.config.guild(ctx.guild).autoroles()
        maybe_not_found = []
        message = ""
        for role in all_roles:
            fetched_role = ctx.guild.get_role(role)
            if not fetched_role:
                maybe_not_found.append(role)
                continue
            message += "- {name} (`{id}`).\n".format(name=fetched_role.name, id=fetched_role.id)
        if maybe_not_found:
            clean_list = list(set(all_roles) - set(maybe_not_found))
            await self.config.guild(ctx.guild).autoroles.set(clean_list)
            message += "\nEinige Rollen wurden entfernt, da ich sie nicht mehr finden konnte."
        if message:
            for line in pagify(message):
                await ctx.send(line)
        else:
            await ctx.send("Es wurde keine Rolle hinzugefügt.")

    # Agreeing command

    @commands.command(name="agree", aliases=["verify"])
    @commands.bot_has_permissions(manage_roles=True, manage_messages=True)
    async def verify_agree(self, ctx: commands.Context):
        """
        Wenn du dem zustimmst, bedeutet das, dass du die Regeln des Servers verstanden hast..
        """
        author = ctx.author
        joined_at = author.joined_at
        member_joined, since_joined = (
            author.joined_at.strftime("%d %b %Y %H:%M"),
            (ctx.message.created_at - joined_at).days,
        )
        member_created, since_created = (
            author.created_at.strftime("%d %b %Y %H:%M"),
            (ctx.message.created_at - author.created_at).days,
        )
        created_on = "{}\n({} days ago)".format(member_created, since_created)
        joined_on = "{}\n({} days ago)".format(member_joined, since_joined)
        author_avatar = author.avatar_url_as(static_format="png")

        data = await self.config.guild(ctx.guild).all()
        log_config = data["logs"]

        if not data["temprole"] and not data["autoroles"]:
            await ctx.send(
                (
                    "Es ist leider keine Rollenkonfiguration eingestellt. Bitte kontaktiere die Moderation "
                    "Team dieses Servers."
                ),
                delete_after=60,
            )
            self.log.warning("Keine Rolle festgelegt. Überprüfung kann nicht verarbeitet werden.")
            return

        try:
            result = await self._handle_role(author)
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send(
                "Error: Ich kann deine Rolle nicht entfernen. Bitte kontaktiere das Moderationsteam.."
            )
            return self.log.warning("Error: Keine Berechtigung zum Entfernen von Rollen.")
        except discord.HTTPException as e:
            return self.log.warning("HTTPException: {} - {}".format(e.status, e.code))
        if log_config is not None:
            embed = discord.Embed(color=discord.Color.green())
            embed.title = "{}#{} - Geprüft".format(author.name, author.discriminator)
            embed.set_thumbnail(url=author_avatar)
            embed.set_footer(text="User ID: {}".format(author.id))
            embed.add_field(name="Kontoerstellung:", value=created_on, inline=True)
            embed.add_field(name="Beitrittsdatum:", value=joined_on, inline=True)
            embed.add_field(name="Status:", value=result[1], inline=True)
            try:
                await ctx.bot.get_channel(log_config).send(embed=embed)
            except discord.Forbidden:
                return self.log.warning(
                    "Error: Logmeldung kann nicht gesendet werden an {}".format(
                        ctx.bot.get_channel(log_config)
                    )
                )
            except discord.HTTPException as e:
                return self.log.warning("HTTPException: {} - {}".format(e.status, e.code))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if await self.bot.cog_disabled_in_guild(self, member.guild):
            return False

        toggle = await self.config.guild(member.guild).toggle()
        role_config = await self.config.guild(member.guild).temprole()
        if toggle is False:
            return False

        if role_config is not None:
            role = discord.utils.get(member.guild.roles, id=int(role_config))
            try:
                await member.add_roles(role, reason="Neues Mitglied, muss überprüft werden.")
            except discord.Forbidden:
                return self.log.warning("Dem neuen Teilnehmer können keine Rollen zugewiesen werden.")
            except discord.HTTPException as e:
                return self.log.warning("HTTPException: {} - {}".format(e.status, e.code))

    async def _handle_role(self, member: discord.Member) -> tuple:
        """Funktion, um einem Mitglied eine Rolle zu geben und/oder zu entfernen.
        Die Rollen werden automatisch aus der Konfiguration des Servers übernommen.
        Parameter:
            member: discord.Member, Das Mitglied, auf das wir einwirken wollen.
        Rückgabe:
            In einem Tupel:
            - bool: True, wenn das Hinzufügen/Entfernen der Rolle erfolgreich war, sonst False.
            - str: Ein String, der für die Protokolle verwendet wird.
        Auslösen:
            discord.Forbidden: Fehlende Berechtigungen für die Bearbeitung von Rollen.
        """
        list_to_add = await self.config.guild(member.guild).autoroles()
        list_to_remove = await self.config.guild(member.guild).temprole()
        actions = []
        if list_to_add:
            for role in list_to_add:
                to_add = member.guild.get_role(role)
                await member.add_roles(to_add, reason="Hinzufügen einer automatischen Rolle durch Verify.")
            actions.append(
                "automatisch hinzugefügt Rolle{plural}".format(
                    plural="s" if len(list_to_add) > 1 else ""
                )
            )
        if list_to_remove:
            to_remove = member.guild.get_role(list_to_remove)
            if to_remove in member.roles:
                await member.remove_roles(to_remove, reason="Entfernen der temporären Rolle durch Verify.")
                actions.append("temporäre Rolle entfernt")
        return (
            True,
            humanize_list(actions).capitalize() if actions else "Es wurde nichts unternommen.",
        )

    async def _maybe_update_config(self):
        if not await self.config.version():  # We never had a version before
            guild_dict = await self.config.all_guilds()
            async for guild_id, info in AsyncIter(guild_dict.items()):
                old_temporary_role = info.get("role", None)
                if old_temporary_role:
                    await self.config.guild_from_id(guild_id).temprole.set(old_temporary_role)
                    await self.config.guild_from_id(guild_id).role.clear()
            await self.config.version.set("1.0.0")
