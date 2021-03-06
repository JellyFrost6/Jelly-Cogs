#   Copyright 2017-present Michael Hall
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import annotations

import re
from typing import NamedTuple

import discord
from redbot.core import commands

from .helpers import embed_from_msg, find_messages

CHANNEL_RE = re.compile(r"^<#(\d{15,21})>$|^(\d{15,21})$")


class GlobalTextChannel(NamedTuple):
    matched_channel: discord.TextChannel

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str):

        bot = ctx.bot

        match = CHANNEL_RE.match(argument)
        channel = None
        if match:
            idx = next(filter(None, match.groups()), None)

            if idx:
                channel_id = int(idx)
                channel = bot.get_channel(channel_id)

        if not channel or not isinstance(channel, discord.TextChannel):
            raise commands.BadArgument('Kanal "{}" nicht gefunden.'.format(argument))

        return cls(channel)


class QuoteTools(commands.Cog):
    """
    Cog for quoting messages by ID
    """

    __author__ = "Jelly"
    __version__ = "2021.03"

    async def red_delete_data_for_user(self, **kwargs):
        """ Nichts zu löschen """
        return

    def format_help_for_context(self, ctx):
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\nCog Version: {self.__version__}"

    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

    @commands.command()
    async def quote(
        self, ctx, channels: commands.Greedy[GlobalTextChannel] = None, *messageids: int
    ):
        """
        erhält (eine) Nachricht(en) nach ID(s)
        Der Nutzer muss die Nachricht(en) sehen können
        Du musst bestimmte Kanäle für die Suche angeben (nur nach ID oder Erwähnung!)
        """

        if not messageids or not channels:
            return await ctx.send_help()

        chans = [c.matched_channel for c in channels]

        msgs = await find_messages(ctx, messageids, chans)
        if not msgs:
            return await ctx.maybe_send_embed("Keine passende Nachricht gefunden.")

        for m in msgs:
            if await ctx.embed_requested():
                em = embed_from_msg(m)
                await ctx.send(embed=em)
            else:
                msg1 = "\n".join(
                    [
                        f"Author: {m.author}({m.author.id})",
                        f"Channel: <#{m.channel.id}>",
                        f"Time(UTC): {m.created_at.isoformat()}",
                    ]
                )
                if len(msg1) + len(m.clean_content) < 2000:
                    await ctx.send(msg1 + m.clean_content)
                else:
                    await ctx.send(msg1)
                    await ctx.send(m.clean_content)
