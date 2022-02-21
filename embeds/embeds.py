import discord
from typing import Optional
from redbot.core import commands, checks
from redbot.core.i18n import Translator, cog_i18n

_ = Translator("Embeds", __file__)

@cog_i18n(_)
class Embeds(commands.Cog):
    """Sends embeds."""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.guild_only()
    @checks.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(embed_links=True)

    async def sendembed(self, ctx, title, text):
        """Embed senden.
        
        Die Einbettung enthält einen Titel `title` und einen Textkörper mit `text`.
        Alle normalen Discord-Formatierungen funktionieren innerhalb der Einbettung.
        Vergiss nicht, jedes Argument in `" "` zu setzen.
        Wenn du ein Bild anhängen möchtest, füge es einfach der Nachricht hinzu."""
        if ctx.message.attachments:
            embed = discord.Embed(
                title = title,
                description = text,
                color = await ctx.embed_color()
            )

            embed.set_image(url=ctx.message.attachments[0].url)

            await ctx.send(embed=embed)

            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

        else:
            embed = discord.Embed(
                title = title,
                description = text,
                color = await ctx.embed_color()
            )

            await ctx.send(embed=embed)
            
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
