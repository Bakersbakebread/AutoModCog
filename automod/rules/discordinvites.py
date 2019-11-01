import discord
import re
from redbot.core import commands
from .base import BaseRule

from ..utils import *

from .base import BaseRuleCommands
from redbot.core import commands

# class DiscordInviteCommands(BaseRuleCommands):
#     # re.search("(https?:\/\/)?(www\.)?((discordapp\.com/invite)|(discord\.gg))\/(\w+)", x)
#     @commands.command(name="tesst")
#     async def _this_is_test(self, ctx):
#         await ctx.send('test')


class DiscordInviteRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)
        self.name = "discordinvite"
