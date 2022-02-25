  
from redbot.core import commands
import discord

old_info = None

class Info(commands.Cog):
    """info stuff"""

    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        global old_info
        if old_info:
            try:
                self.bot.remove_command("info")
            except:
                pass
            self.bot.add_command(old_info)

    @commands.bot_has_permissions(embed_links=True)
    @commands.command()
    async def info(self, ctx):
       """invite"""
       embed=discord.Embed(color=0x00fbff)
       embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/762976674659696660/f9954b81eb0548102bc46713623f9291.png?size=1024")
       embed.add_field(name="Owner of Toli:", value="Jelly", inline=True)
       embed.add_field(name="Python:", value="[3.8.7](https://www.python.org/)", inline=True)
       embed.add_field(name="discord.py", value="[1.6.0](https://github.com/Rapptz/discord.py)", inline=True)
       embed.add_field(name="Red version:", value="[3.4.7a69.dev26](https://pypi.org/project/Red-DiscordBot)", inline=False)
       embed.add_field(name="About Red:", value="Toli is a customized instance of [Red](https://github.com/Cog-Creators/Red-DiscordBot), made by [Twentysix](https://github.com/Twentysix26) and improved by [many](https://github.com/Cog-Creators).", inline=False)
       await ctx.send(embed=embed)

def setup(bot):
    info = Info(bot)
    global old_info
    old_info = bot.get_command("info")
    if old_info:
        bot.remove_command(old_info.name)
    bot.add_cog(info)
