from redbot.core.commands import Converter, BadArgument
from redbot.core.utils.chat_formatting import box

from cogs.CogManager.AutoModCog.automod.utils import error_message


class ToggleBool(Converter):
    available_yes = ['y', 'yes', 'yeh', 'true', 'enable', 'activate']
    available_no = ['n', 'no', 'nah', 'false', 'disable', 'deactivate']
    async def convert(self, ctx, argument):
        argument = argument.lower()

        if argument in self.available_yes:
            return True

        if argument in self.available_no:
            return False

        nl = "\n"
        fmt_box = box(
            f"+ To enable\n"
                      f"{', '.join(self.available_yes)}\n\n"
                      f"- To disable\n"
                      f"{', '.join(self.available_no)}\n"
            f"\n--- ᴄᴀsᴇ ɪɴsᴇɴsɪᴛɪᴠᴇ ---\n", "diff")
        raise BadArgument(await error_message(f" `{argument}` is not valid. Allowed values are:\n{fmt_box}\n"))
