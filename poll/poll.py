#from discord.ext import commands
from redbot.core import commands, Config, checks
from datetime import datetime
import discord
import asyncio
import json

def to_emoji(c):
    base = 0x1f1e6
    return chr(base + c)

class poll(commands.Cog, name='poll'):
    """Dieses Modul ist für die Umfragen zuständig."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def poll(self, ctx, channel : discord.TextChannel):
        """Dieser Befehl erstellt eine Umfrage. Benutze die Reaktionen, um abzustimmen.
        **Beispiel: *>poll #channel***"""

        e = discord.Embed(color = await ctx.embed_color())
        e.timestamp = datetime.utcnow()
        messages = [ctx.message]
        answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) <= 100

        await ctx.send("**Bitte schreibe die Frage auf:**")
        try:
            question = await self.bot.wait_for('message', check=check, timeout=60.0)
            question = question.content
        except:
            return


        for i in range(20):
            messages.append(await ctx.send(f'**Antwortoptionen oder Typ angeben `{ctx.prefix}publish` um die Umfrage zu veröffentlichen.**'))
            try:
                entry = await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                break
            messages.append(entry)
            if entry.clean_content.startswith(f'{ctx.prefix}publish'):
                break
            answers.append((to_emoji(i), entry.clean_content))

        try:
            await ctx.channel.delete_messages(messages)
        except Exception as e:
            print(f'ERROR: Die Nachricht kann nicht gelöscht werden - {e}')

        answer = '\n'.join(f'{keycap}: {content}' for keycap, content in answers)
        e.description = f'**{question}**\n\n{answer}'
        e.set_footer(text = ctx.author)
        actual_poll = await channel.send(embed=e)
        for emoji, _ in answers:
            await actual_poll.add_reaction(emoji)

    @poll.error
    async def poll_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send('**Der Kanal fehlt.**')

    @commands.command()
    @commands.guild_only()
    async def quickpoll(self, ctx, *questions_and_choices: str):
        """Dieser Befehl erstellt eine Schnellumfrage. Das erste Argument ist die Frage, alle anderen sind Antworten.
        **Beispiel: *>quickpoll "Question?" "Answer 1" "Answer 2"***"""
        embed = discord.Embed(color = await ctx.embed_color())
        embed.timestamp = datetime.utcnow()
        if len(questions_and_choices) < 3:
            return await ctx.send('**Du brauchst mindestens 1 Frage mit 2 Auswahlmöglichkeiten.**')
        elif len(questions_and_choices) > 21:
            return await ctx.send('**Du kannst nur bis zu 20 Auswahlmöglichkeiten haben.**')
        perms = ctx.channel.permissions_for(ctx.me)
        if not (perms.read_message_history or perms.add_reactions):
            return await ctx.send('**Ich brauche die Berechtigung "Nachrichtenverlauf lesen" und "Reaktion hinzufügen".**')
        question = questions_and_choices[0]
        choices = [(to_emoji(e), v) for e, v in enumerate(questions_and_choices[1:])]
        try:
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f'ERROR: Die Nachricht kann nicht gelöscht werden - {e}')

        body = "\n".join(f"{key}: {c}" for key, c in choices)
        embed.description = f"**{question}**\n\n{body}"
        embed.set_footer(text = ctx.author)
        poll = await ctx.send(embed=embed)
        for emoji, _ in choices:
            await poll.add_reaction(emoji)
