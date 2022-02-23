from contextlib import suppress
from typing import Union

import discord
from redbot.core import Config, checks
from redbot.core.commands import commands, Context

BaseCog = getattr(commands, "Cog", object)


class Reaktionsrollen(BaseCog):
    """Dieses Rädchen gewährt oder entfernt Rollen, indem es eine Reaktion auf eine Nachricht hinzufügt."""

    def __init__(self, bot):
        self.bot = bot
        self.settings = Config.get_conf(self, 93843927132)
        default_guild_settings = {
            "reaction_roles": {}
        }
        self.settings.register_guild(**default_guild_settings)

    def _get_emoji(self, emoji):
        try:
            emoji = int(emoji)
            emoji = self.bot.get_emoji(emoji)
            return emoji
        except ValueError:
            return emoji

    @commands.group(name='rr')
    @checks.admin_or_permissions(manage_guild=True)
    async def reaktionsrollen(self, ctx: Context):
        """Verwaltung der Reaktionsrollen"""
        pass

    @reaktionsrollen.command(name='add')
    async def reaktionsrollen_add(self, ctx: Context, message: discord.Message, emoji: Union[discord.Emoji, str],
                                  role: discord.Role):
        """Füge eine Reaktionsrolle hinzu."""
        # TODO: Check permissions if the bot is able to grant the role
        reaktionsrollen = await self.settings.guild(ctx.guild).reaktionsrollen()
        message_indicator = f'{message.channel.id}:{message.id}'
        raw_emoji = str(emoji.id if isinstance(emoji, discord.Emoji) else emoji)

        if message_indicator in reaktionsrollen:
            if raw_emoji in reaktionsrollen[message_indicator]:
                embed = discord.Embed(colour=discord.Colour.dark_red())
                embed.description = f'Es ist bereits eine Reaktionsrolle mit diesem Emoji registriert.\n' \
                                    f'> Emoji: {emoji}\n' \
                                    f'> Message: {message.jump_url}'
                return await ctx.send(embed=embed)
        else:
            reaktionsrollen[message_indicator] = {}

        try:
            await message.add_reaction(emoji)
        except discord.Forbidden:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'I could\'t add a reaction to the message due to missing permissions.\n' \
                                f'> Emoji: {emoji}\n' \
                                f'> Message: {message.jump_url}'
            return await ctx.send(embed=embed)

        reaktionsrollen[message_indicator][raw_emoji] = role.id
        await self.settings.guild(ctx.guild).reaktionsrollen.set(reaktionsrollen)
        embed = discord.Embed(colour=discord.Colour.green())
        embed.description = f'Die Reaktionsrolle wurde erfolgreich hinzugefügt.\n' \
                            f'> Emoji: {emoji}\n' \
                            f'> Message: {message.jump_url}\n' \
                            f'> Role: {role.mention}'
        return await ctx.send(embed=embed)

    @reaktionsrollen.command(name='remove')
    async def reaktionsrollen_remove(self, ctx: Context, message: discord.Message, emoji: Union[discord.Emoji, str]):
        """Entferne eine Reaktionsrolle."""
        reaktionsrollen = await self.settings.guild(ctx.guild).reaktionsrollen()
        message_indicator = f'{message.channel.id}:{message.id}'
        raw_emoji = str(emoji.id if isinstance(emoji, discord.Emoji) else emoji)

        if message_indicator not in reaktionsrollen or raw_emoji not in reaction_roles[message_indicator]:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'Für dieses Emoji ist keine Reaktionsrolle registriert.\n' \
                                f'> Emoji: {emoji}\n' \
                                f'> Message: {message.jump_url}'
            return await ctx.send(embed=embed)

        with suppress(discord.Forbidden):
            await message.remove_reaction(emoji, ctx.guild.me)

        del reaktionsrollen[message_indicator][raw_emoji]
        if len(reaktionsrollen[message_indicator]) == 0:
            del reaktionsrollen[message_indicator]
        await self.settings.guild(ctx.guild). reaktionsrollen.set(reaktionsrollen)
        embed = discord.Embed(colour=discord.Colour.dark_blue())
        embed.description = f'Die Reaktionsrolle wurde erfolgreich entfernt.\n' \
                            f'> Emoji: {emoji}\n' \
                            f'> Message: {message.jump_url}'
        return await ctx.send(embed=embed)

    @reaktionsrollen.command(name='list')
    async def  reaktionsrollen_list(self, ctx: Context):
        """List all setup reaction roles."""
        reaktionsrollen = await self.settings.guild(ctx.guild).reaktionsrollen()
        if len(reaktionsrollen) == 0:
            embed = discord.Embed(colour=discord.Colour.dark_red())
            embed.description = f'Es ist keine Reaktionsrolle für diesen Server eingerichtet.'
            return await ctx.send(embed=embed)

        embed = discord.Embed(colour=discord.Colour.dark_magenta())
        for message_indicator, message_data in reaktionsrollen.items():
            split = message_indicator.split(':')
            channel = self.bot.get_channel(int(split[0]))
            try:
                message = await channel.fetch_message(int(split[1]))
            except discord.NotFound:
                continue
            reactions = []
            for raw_emoji, role_id in message_data.items():
                emoji = self._get_emoji(raw_emoji)
                role = ctx.guild.get_role(role_id)
                reactions.append(f'{emoji} **-** {role.mention}')
            embed.add_field(name=message.jump_url, value='\n'.join(reactions), inline=False)
        return await ctx.send(embed=embed)

    async def get_role(self, payload: discord.RawReactionActionEvent):
        message_indicator = f'{payload.channel_id}:{payload.message_id}'
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return None
        reaktionsrollen = await self.settings.guild(guild).reaktionsrollen()
        if message_indicator not in reaktionsrollen:
            return None
        emoji = str(payload.emoji.id if payload.emoji.is_custom_emoji() else payload.emoji)
        if emoji not in reaktionsrollen[message_indicator]:
            return None
        role = guild.get_role(reaktionsrollen[message_indicator][emoji])
        if not role:
            return None
        return role

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return
        role = await self.get_role(payload)
        if not role:
            return
        with suppress(discord.Forbidden):
            await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member:
            return
        role = await self.get_role(payload)
        if not role:
            return
        with suppress(discord.Forbidden):
            await member.remove_roles(role)
