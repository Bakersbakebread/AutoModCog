import discord
from .base import BaseRule


class WallSpamRule(BaseRule):
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
