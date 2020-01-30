import discord
from redbot.core import commands, checks
from .constants import *
from .utils import *
from .converters import ToggleBool

groups = {
    "mentionspamrule": "Mention spam",
    "wallspamrule": "Wall spam",
    "inviterule": "Discord invites",
    "spamrule": "General spam",
    "maxwordsrule": "Maximum words",
    "maxcharsrule": "Maximum characters",
}

# thanks Jackenmen#6607 <3


class GroupCommands:

    # commands specific to maxwords
    @commands.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def maxwordsrule(self, ctx):
        """
        Detects the maximum allowed length of individual words in a single message
        """
        pass

    @maxwordsrule.command(name="threshold")
    @checks.mod_or_permissions(manage_messages=True)
    async def _maxwords_threshold(self, ctx, max_length: int):
        """Set the threshold for the amount of individual words allowed

        For example, if the threshold is set to 4 this sentence would be caught:

        `The quick brown fox`
        """
        await self.maxwordsrule.set_max_words_length(ctx.guild, max_length)
        await ctx.send(f"`💬` The maximum number of words in one message is set to `{max_length}`")

    # commands specific to maxchars
    @commands.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def maxcharsrule(self, ctx):
        """Detects the maximum allowed individual characters in a single message"""
        pass

    @maxcharsrule.command(name="threshold")
    @checks.mod_or_permissions(manage_messages=True)
    async def _max_chars_threshold(self, ctx, max_length: int):
        """Set the threshold for the amount of individual characters allowed

        For example, if the threshold is set to 10 this sentence would be caught:

        `This is too long`
        """
        await self.maxcharsrule.set_max_chars_length(ctx.guild, max_length)
        await ctx.send(
            f"`💬` The maximum number of characters in one message is set to `{max_length}`"
        )

    # commands specific to spamrule
    @commands.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def spamrule(self, ctx):
        """
        Mass spamming by user or content

        1) It checks if a user has spammed more than 10 times in 12 seconds
        2) It checks if the content has been spammed 15 times in 17 seconds.
        """
        pass

    # commands specific to mention spam rule
    @commands.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def mentionspamrule(self, ctx):
        """Individual mentions spam settings"""
        pass

    @mentionspamrule.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def threshold(self, ctx, threshold: int):
        """Set the max amount of individual mentions allowed

        This overrides the default number of 4 individual mentions on the Mention Spam rule
        """
        before, after = await self.mentionspamrule.set_threshold(ctx, threshold)
        await ctx.send(f"`🎯` Mention threshold changed from `{before}` to `{after}`")

    # commands specific to wall spam rule
    @commands.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def wallspamrule(self, ctx):
        """Walls of text/emojis settings"""
        pass

    # commands specific to discord invite rule
    @commands.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def inviterule(self, ctx):
        """Filters discord invites

        Supported type of discord links:
        `discord.gg/inviteCode`
        `discordapp.com/invite/inviteCode`
        """
        pass

    @inviterule.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def whitelistlink(self, ctx):
        """Add/remove/show links allowed

        Adding a link to the whitelist will allow it to be immune from automod actions"""
        pass

    @whitelistlink.command(name="add")
    @checks.mod_or_permissions(manage_messages=True)
    async def add_link(self, ctx, link: str):
        """
        Add a link to not be filtered.

        This must be the full link, supported types:

        discord.gg/inviteCode
        discordapp.com/invite/inviteCode
        """
        try:
            await self.inviterule.add_allowed_link(ctx.guild, link)
        except ValueError:
            return await ctx.send("`👆` That link already exists.")

        return await ctx.send(f"`👍` Added `{link}` to the allowed links list.")

    @whitelistlink.command(name="delete")
    @checks.mod_or_permissions(manage_messages=True)
    async def delete_link(self, ctx, link: str):
        """
        Deletes a link from the ignore list

        This must be the full exact match of a link in the list.
        """
        try:
            await self.inviterule.delete_allowed_link(ctx.guild, link)
        except ValueError as e:
            await ctx.send(f"`❌` {e.args[0]}")

    @whitelistlink.command(name="show")
    @checks.mod_or_permissions(manage_messages=True)
    async def show_links(self, ctx):
        """
        Show a list of links that are not filtered.
        """
        allowed_links = await self.inviterule.get_allowed_links(ctx.guild)
        if allowed_links is not None:
            embed = discord.Embed(
                title="Links that are not filtered by the rule",
                description=", ".join("`{0}`".format(w) for w in allowed_links),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"`❌` No links currently allowed.")


def enable_rule_wrapper(group, name, friendly_name):
    @group.command(name="toggle")
    @checks.mod_or_permissions(manage_messages=True)
    async def enable_rule(self, ctx, toggle: ToggleBool):
        """
        Toggle enabling/disabling this rule

        """
        rule = getattr(self, name)
        is_enabled = await rule.is_enabled(ctx.guild)
        if toggle is None:
            return await ctx.send(f"{name} is `{transform_bool(is_enabled)}`.")

        if is_enabled == toggle:
            return await ctx.send(f"{name} is already `{transform_bool(is_enabled)}`")

        before, after = await rule.toggle_enabled(ctx.guild, toggle)
        await ctx.send(
            f"**{friendly_name.title()}** set from `{transform_bool(before)}` to `{transform_bool(after)}`"
        )

    return enable_rule


def action_to_take__wrapper(group, name, friendly_name):
    @group.command(name="action")
    @checks.mod_or_permissions(manage_messages=True)
    async def action_to_take(self, ctx):
        """
        Choose which action to take on an offensive message

       1) Nothing (still fires event for third-party integration)
       2) DM a role\n
       3) Add a role to offender (Mute role for example)
       4) Kick offender
       5) Ban offender
        """
        rule = getattr(self, name)
        embed = discord.Embed(
            title="What action should be taken against wallspam?",
            description=f":one: Nothing (still fires event for third-party integration)\n"
            f":two: DM a role\n"
            f":three: Add a role to offender (Mute role for example)\n"
            f":four: Kick offender\n"
            f":five: Ban offender",
        )
        action = await get_option_reaction(ctx, embed=embed)
        if action:
            await ctx.send(await thumbs_up_success(ACTION_CONFIRMATION[action]))
            await rule.set_action_to_take(action, ctx.guild)
        else:
            await ctx.send("Okay, nothing's changed.")

    return action_to_take


def delete_message_wrapper(group, name, friendly_name):
    @group.command(name="delete")
    @checks.mod_or_permissions(manage_messages=True)
    async def delete_message(self, ctx):
        """
        Toggles whether message should be deleted on offence

        `manage_messages` perms are needed for this to run.
        """
        rule = getattr(self, name)
        before, after = await rule.toggle_to_delete_message(ctx.guild)
        await ctx.send(
            f"Deleting messages set from `{transform_bool(before)}` to `{transform_bool(after)}`"
        )

    return delete_message


def whitelist_wrapper(group, name, friendly_name):
    @group.group(name="whitelistrole")
    @checks.mod_or_permissions(manage_messages=True)
    async def whitelistrole(self, ctx):
        """Whitelisting roles settings

        Adding a role to the whitelist means that this role will be immune to automod actions
        """
        pass

    return whitelistrole


def whitelistrole_add_wrapper(group, name, friendly_name):
    @group.command(name="add")
    @checks.mod_or_permissions(manage_messages=True)
    async def whitelistrole_add(self, ctx, role: discord.Role):
        """
                Add a role to be ignored by automod actions"

                Passing a role already whitelisted will prompt for deletion
                """
        rule = getattr(self, name)
        try:
            await rule.append_whitelist_role(ctx.guild, role)
        except ValueError:
            await ctx.send(f"`{role}` is already whitelisted.", delete_after=30)
            result = await yes_or_no(ctx, f"Would you like to remove `{role}` from the whitelist?")
            if result:
                await rule.remove_whitelist_role(ctx.guild, role)
        await ctx.send(f"`{role}` added to the whitelist.")

    return whitelistrole_add


def whitelistrole_delete_wrapper(group, name, friendly_name):
    @group.command(name="delete")
    @checks.mod_or_permissions(manage_messages=True)
    async def whitelistrole_delete(self, ctx, role: discord.Role):
        """Delete a role from being ignored by automod actions"""
        rule = getattr(self, name)
        try:
            await rule.remove_whitelist_role(ctx.guild, role)
        except ValueError:
            return await ctx.send(f"`{role}` is not whitelisted.")

    return whitelistrole_delete


def whitelistrole_show_wrapper(group, name, friendly_name):
    @group.command(name="show")
    @checks.mod_or_permissions(manage_messages=True)
    async def whitelistrole_show(self, ctx):
        """Show all whitelisted roles"""
        rule = getattr(self, name)
        all_roles = await rule.get_all_whitelisted_roles(ctx.guild)
        if all_roles:
            desc = ", ".join("`{0}`".format(role) for role in all_roles)
            em = discord.Embed(
                title="Whitelisted roles", description=desc, color=discord.Color.greyple(),
            )
            await ctx.send(embed=em)
        else:
            await ctx.send("`❌` No roles currently whitelisted.")

    return whitelistrole_show


def add_role_wrapper(group, name, friendly_name):
    @group.command(name="role")
    @checks.mod_or_permissions(manage_messages=True)
    async def add_role(self, ctx, role: discord.Role):
        """
        Set the role to add to offender

        When a rule offence is found and action to take is set to "Add Role", this role is the one that will be added.
        """
        rule = getattr(self, name)
        before, after = await rule.set_mute_role(ctx.guild, role)

        await ctx.send(f"Role to add set from `{before}` to `{after}`")

    return add_role


def add_channel_wrapper(group, name, friendly_name):
    @group.command(name="channels")
    @checks.mod_or_permissions(manage_messages=True)
    async def add_channel(self, ctx, channels: commands.Greedy[discord.TextChannel]):
        """
        Set the channels to enforce this rule on.

        The default setting is global, passing nothing will reset to global.
        """
        rule = getattr(self, name)
        set_channels = await rule.set_enforced_channels(ctx.guild, channels)
        if not channels:
            should_clear = await yes_or_no(ctx, "Would you like to clear the channels?")
            if should_clear:
                channels = []
            else:
                return await ctx.send("Okay, no channels changed.")
        elif not channels:
            return await ctx.send("Please send me which channels you would like to enforce.")

        enforcing = await rule.set_enforced_channels(ctx.guild, channels)
        enforcing_string = "\n".join(
            "• `{0}`".format(ctx.guild.get_channel(channel)) for channel in enforcing
        )
        await ctx.send(f"Okay, done. Enforcing these channels:\n{enforcing_string}")

    return add_channel

def settings_wrapper(group, name, friendly_name):
    @group.command(name="settings")
    @checks.mod_or_permissions(manage_messages=True)
    async def _invoke_settings(self, ctx):
        """
        Show settings for this rule
        """
        rule = getattr(self, name)
        await ctx.invoke(self.bot.get_command(f"automodset show"), name)

    return _invoke_settings


for name, friendly_name in groups.items():
    group = getattr(GroupCommands, name)

    settings = settings_wrapper(group, name, friendly_name)
    settings.__name__ = f"settings_{name}"
    setattr(GroupCommands, f"settings_{name}", settings)

    enable_rule = enable_rule_wrapper(group, name, friendly_name)
    enable_rule.__name__ = f"enable_{name}"
    setattr(GroupCommands, f"enable_{name}", enable_rule)

    action_to_take = action_to_take__wrapper(group, name, friendly_name)
    action_to_take.__name__ = f"action_{name}"
    setattr(GroupCommands, f"action_{name}", action_to_take)

    delete_message = delete_message_wrapper(group, name, friendly_name)
    delete_message.__name__ = f"delete_{name}"
    setattr(GroupCommands, f"delete_{name}", delete_message)

    # whitelist settings
    # whitelist commands inherit whitelist role group
    whitelistrole = whitelist_wrapper(group, name, friendly_name)
    whitelistrole.__name__ = f"whitelistrole_{name}"
    setattr(GroupCommands, f"whitelistrole_{name}", whitelistrole)

    # whitelist group
    whitelistrole_delete = whitelistrole_delete_wrapper(whitelistrole, name, friendly_name)
    whitelistrole_delete.__name__ = f"whitelistrole_delete_{name}"
    setattr(GroupCommands, f"whitelistrole_delete_{name}", whitelistrole_delete)

    # whitelist group
    whitelistrole_add = whitelistrole_add_wrapper(whitelistrole, name, friendly_name)
    whitelistrole_add.__name__ = f"whitelistrole_add_{name}"
    setattr(GroupCommands, f"whitelistrole_add_{name}", whitelistrole_add)

    # whitelist group
    whitelistrole_show = whitelistrole_show_wrapper(whitelistrole, name, friendly_name)
    whitelistrole_show.__name__ = f"whitelistrole_show_{name}"
    setattr(GroupCommands, f"whitelistrole_show_{name}", whitelistrole_show)

    add_role = add_role_wrapper(group, name, friendly_name)
    add_role.__name__ = f"add_role_{name}"
    setattr(GroupCommands, f"add_role_{name}", add_role)

    add_channel = add_channel_wrapper(group, name, friendly_name)
    add_channel.__name__ = f"add_role_{name}"
    setattr(GroupCommands, f"add_role_{name}", add_channel)
