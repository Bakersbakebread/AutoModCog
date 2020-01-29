import discord

from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils.menus import start_adding_reactions


async def maybe_add_role(user: discord.Member, role: discord.Role):
    """Adds role to user, if the user already has the role fails silently"""
    has_role = any(role == r.id for r in user.roles)
    if has_role:
        return
    await user.add_roles(role, reason="Automod rule add")


async def thumbs_up_success(message: str):
    return f"`👍🏼` {message}"


async def error_message(message: str):
    return f"`❌` {message}"


async def action_to_take_mapping(index):
    actions = {0: "third_party", 1: "message", 2: "add_role", 3: "kick", 4: "ban"}
    return actions[index]


async def get_option_reaction(ctx, message: str = None, embed: discord.Embed = None):
    if not embed:
        msg = await ctx.send(message, delete_after=30)
    else:
        msg = await ctx.send(embed=embed, delete_after=30)
    emojis = ReactionPredicate.NUMBER_EMOJIS[1:6]
    # Action 1: Do Nothing (still fire event)
    # Action 2: Message
    # Action 3 : Add Role
    # Action 4: Kick
    # Action 5: Ban
    start_adding_reactions(msg, emojis)

    pred = ReactionPredicate.with_emojis(emojis, msg, ctx.author)
    react = await ctx.bot.wait_for("reaction_add", check=pred)
    return await action_to_take_mapping(pred.result)


async def yes_or_no(ctx, message) -> bool:
    msg = await ctx.send(message)
    start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)

    pred = ReactionPredicate.yes_or_no(msg, ctx.author)
    await ctx.bot.wait_for("reaction_add", check=pred)
    await msg.delete()
    return pred.result


def transform_bool(is_enabled):
    return "Enabled" if is_enabled else "Disabled"
