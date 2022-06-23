from copy import copy
from pathlib import Path
from typing import List, Optional

from telegram import Update, Message
from telegram.ext import CommandHandler, CallbackContext

from lib.basic import HelpInfo, ExtHandler, PageDescription
from lib.utils import send_message, render_list, read_page_from_dir, subdirs, flatten

COMMANDS_LIST = "COMMANDSLIST"


class ShowPageCommand(ExtHandler, CommandHandler):
    def __init__(self, page_description: PageDescription, super_commands: List[str], sub_commands: List[HelpInfo],
                 separator=' '):
        self.page_description = page_description
        self.super_commands = super_commands
        self.subcommands = sub_commands
        self.separator = separator
        self.command_string = self.separator.join(self.super_commands + [self.page_description.command])
        self.cur_level_command_string = self.page_description.command

        super().__init__(self.command_string, self.create_page)

    def is_visible_in_help(self, help_message: Message):
        # we show only top-level pages
        return len(self.super_commands) == 0

    def get_subcommands(self, update: Update, context: CallbackContext):
        return self.subcommands

    def create_page(self, update: Update, context: CallbackContext):
        text = copy(self.page_description.text)

        # TODO: make pattern for possible commands injection
        if len(self.get_subcommands(update, context)) > 0:
            list_items = ["/" + info.command_string.replace("_", "\\_") + f" : {info.description}" for info in self.get_subcommands(update, context)]

            if text.find(COMMANDS_LIST) < 0:
                text += f"\n{COMMANDS_LIST}"

            text = text.replace(COMMANDS_LIST, render_list(list_items))

        send_message(update, text, self.page_description.photo)

    def get_help_info(self) -> Optional[HelpInfo]:
        return HelpInfo(command_string=self.command_string,
                        description=self.page_description.short_text)


def process_hierarchy(root_path: Path, command_separator=' ', prev_commands: List[str] = []) -> List[ShowPageCommand]:
    descr = read_page_from_dir(root_path)

    descendants_handlers = [
        process_hierarchy(d, prev_commands=prev_commands + [descr.command], command_separator=command_separator) for d
        in subdirs(root_path)]
    direct_descendants_command_strings = [desc[0].get_help_info() for desc in descendants_handlers]

    cur_handler = ShowPageCommand(page_description=descr,
                                  sub_commands=direct_descendants_command_strings,
                                  super_commands=prev_commands,
                                  separator=command_separator)

    return [cur_handler] + flatten(descendants_handlers)

