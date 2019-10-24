import discord
from .base import BaseRule

from ..utils import *


from redbot.core import commands


class WallSpamRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)
        self.name = "wallspam"

    async def is_offensive(self, message):
        try:
            message_split = message.content.split()
            is_wall_text = (
                sum((item.count(message_split[0]) for item in message_split)) > 25
            )
            is_maybe_wall_text = len(message_split[0]) > 800

            if is_wall_text or is_maybe_wall_text:
                return True
        except IndexError:
            # probably one word messge.
            pass
