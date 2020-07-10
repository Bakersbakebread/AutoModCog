from abc import ABCMeta, ABC

import discord
import re

from .base import BaseRule


class DiscordInviteRule(BaseRule, ABC):
    def __init__(
        self, config,
    ):
        super().__init__(config)
        self.name = "discordinvite"

    async def get_allowed_links(
        self, guild: discord.Guild,
    ):
        try:
            allowed_links = await self.config.guild(guild).get_raw(
                self.rule_name, "allowed_links",
            )
        except KeyError:
            # no links have been added
            allowed_links = None

        return allowed_links

    async def add_allowed_link(
        self, guild: discord.Guild, link: str,
    ):
        current_links = await self.get_allowed_links(guild)
        if current_links is not None:
            if link in current_links:
                raise ValueError("Link already exists.")
            current_links.append(link)
            await self.config.guild(guild).set_raw(
                self.rule_name, "allowed_links", value=current_links,
            )
        else:
            await self.config.guild(guild).set_raw(
                self.rule_name, "allowed_links", value=[link],
            )

    async def delete_allowed_link(
        self, guild: discord.Guild, link: str,
    ):
        current_links = await self.get_allowed_links(guild)
        if current_links is None or link not in current_links:
            raise ValueError("Link provided is not in the allowed list.")

        current_links.pop(link)
        await self.config.guild(guild).set_raw(
            self.rule_name, "allowed_links", value=current_links,
        )

    async def is_offensive(
        self, message: discord.Message,
    ):
        guild = message.guild
        content = message.content

        allowed_links = await self.get_allowed_links(guild)

        r = re.compile(r"(discord\.(?:gg|io|me|li)|discord(?:app)?\.com\/invite)\/(\S+)", re.I)

        if allowed_links:
            filter_content = [x for x in content.split() if x not in allowed_links]
        else:
            filter_content = content.split()

        has_offensive = list(filter(r.match, filter_content,))

        if has_offensive:
            return True
