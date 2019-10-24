import discord
from redbot.core.config import Config

from ..constants import DEFAULT_ACTION

class BaseRule:
    def __init__(self, config):
        self.config = config
        self.rule_name = type(self).__name__

    async def print_class_name(self):
        print(type(self).__name__)

    async def is_enabled(self, guild: discord.Guild) -> bool or None:
        """Helper to return the status of Rule"""
        try:
            return await self.config.guild(guild).get_raw(self.rule_name, "is_enabled")
        except KeyError:
            return None

    async def toggle_enabled(self, guild: discord.Guild) -> (bool, bool):
        """Toggles whether the rule is in effect"""
        try:
            before = await self.config.guild(guild).get_raw(
                self.rule_name, "is_enabled"
            )
            await self.config.set_raw(self.rule_name, value={"is_enabled": not before})
            return before, not before
        except KeyError:
            await self.config.guild(guild).set_raw(
                self.rule_name, value={"is_enabled": True}
            )
            return False, True

    async def get_action_to_take(self, guild: discord.Guild) -> str:
        """Helper to return what action is currently set on offence"""
        try:
            return await self.config.guild(guild).get_raw(
                self.rule_name, "action_to_take"
            )
        except KeyError:
            await self.config.guild(guild).set_raw(
                    self.rule_name, "action_to_take", value=DEFAULT_ACTION)
            return DEFAULT_ACTION

    async def set_action_to_take(self, action: str, guild: discord.Guild):
        """Sets the action to take on an offence"""
        await self.config.guild(guild).set_raw(
            self.rule_name, "action_to_take", value=action
        )

    async def toggle_to_delete_message(self, guild: discord.Guild) -> (bool, bool):
        """Toggles whether offending message should be deleted"""
        before = await self.config.guild(guild).get_raw(
            self.rule_name, "delete_message"
        )
        await self.config.guild(guild).set_raw(
            self.rule_name, "delete_message", value=not before
        )
        return before, not before

    async def role_is_whitelisted(
        self, guild: discord.Guild, roles: [discord.Role]
    ) -> bool:
        """Checks if role is whitelisted"""
        try:
            whitelist_roles = await self.config.guild(guild).get_raw(
                self.rule_name, "whitelist_roles"
            )
        except KeyError:
            # no roles are whitelisted
            return False

        # return any(role in whitelist_roles for role in [role.id for role in roles])
        for role in roles:
            if role.id in whitelist_roles:
                return True
        return False

    # guild specifics
    async def append_whitelist_role(self, guild: discord.Guild, role: discord.Role):
        """Adds role to whitelist"""
        try:
            roles = await self.config.guild(guild).get_raw(
                self.rule_name, "whitelist_roles"
            )
            if role.id in roles:
                raise ValueError("Role is already whitelisted")

            roles.append(role.id)
            await self.config.guild(guild).set_raw(
                self.rule_name, "whitelist_roles", value=roles
            )

        except KeyError:
            # no roles added yet
            return await self.config.guild(guild).set_raw(
                self.rule_name, "whitelist_roles", value=[role.id]
            )

    async def remove_whitelist_role(self, guild: discord.Guild, role: discord.Role):
        """Removes role from whitelist"""
        roles = await self.config.guild(guild).get_raw(
            self.rule_name, "whitelist_roles"
        )
        roles.remove(role.id)
        await self.config.guild(guild).set_raw(self.rule_name, "whitelist_roles", value=roles)
