import distutils.dir_util
import logging
import os.path
from functools import partial
from pathlib import Path
from typing import Optional

from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.updater import Updater
from telegram.update import Update

from lib.basic import ConfigHolder
from lib.commands.help import HelpCommand
from lib.commands.show_page import process_hierarchy
from lib.utils import read_page_from_dir, subdirs

logger = logging.getLogger()

logging.basicConfig(filename='app.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
logger.addHandler(logging.StreamHandler())

with open("token", mode="r") as f:
    TOKEN = f.readline()


def help(update: Update, context: CallbackContext):
    update.message.reply_text("Help content here")


class Main(object):
    def __init__(self, token, commands_dir: Path, stable_config_dir: Path):
        self.commands_dir = commands_dir
        self.stable_config_dir = stable_config_dir
        self.updater = Updater(token, use_context=True)
        self.handlers = []
        self.load_commands(False, None, None)

    def add_handler(self, handler):
        self.updater.dispatcher.add_handler(handler)
        self.handlers.append(handler)

    def load_commands(self, stable: bool, update: Optional[Update], context):
        if update is not None and update.message.from_user.username not in ConfigHolder.admin_ids:
            return

        if stable and not os.path.isdir(self.stable_config_dir):
            raise Exception("Trying to load non-existing stable configuration.")

        logger.info("Clearing old handlers...")
        for h in self.handlers:
            self.updater.dispatcher.remove_handler(h)
        logger.info("Done.")

        target_path = self.commands_dir if not stable else self.stable_config_dir

        # We always have 'reload' and 'help' commands
        help_page_description = read_page_from_dir(target_path, "help_message.md", "help_pic.jpg")
        help_handler = HelpCommand(help_page_description)
        self.add_handler(help_handler)
        on_load = update is None

        logger.info("Processing command dirs...")
        for subdir in subdirs(target_path):
            try:
                # TODO: add here custom command handlers living in dirs and use 'process hierarchy' only as fallback
                subdir_handlers = process_hierarchy(subdir, command_separator="_")
                help_handler.add_help_info(subdir_handlers[0].get_help_info())
                for h in subdir_handlers:
                    self.add_handler(h)
            except Exception as e:
                if not on_load:
                    update.message.reply_text(
                        f"Error while trying to load new command configuration from dir {subdir.name}. "
                        "See logs for info. Will use previous stable configuration")

                    logger.exception(f"Error while trying to load new command configuration from dir {subdir.name}. ")

                    if not stable:
                        logger.info("Trying to load last stable command configuration...")
                        # load stable config
                        self.load_commands(True, update, context)
                        logger.info("Successfully loaded last stable command configuration.")
                        return

        logger.info("Done processing command dirs.")

        if update is not None:
            logger.info("Running commands to check their correctness...")
            for handlers_group in self.updater.dispatcher.handlers.values():
                for h in handlers_group:
                    try:
                        h.callback(update, context)
                    except Exception as e:
                        s = f"Error while trying to run command {h.command_string}. "
                        update.message.reply_text(
                            s + " See logs for info. Will use previous stable configuration")
                        logger.exception(s)
                        self.load_commands(True, update, context)
                        return
            logger.info("Done.")

        if not stable:
            logger.info("Saving new stable configuration...")
            distutils.dir_util.remove_tree(self.stable_config_dir.name)
            distutils.dir_util.copy_tree(self.commands_dir.name, self.stable_config_dir.name)
            logger.info("Done saving new stable configuration.")

        self.add_handler(CommandHandler('reload', partial(self.load_commands, False)))

    def start(self):
        self.updater.start_polling()


if __name__ == '__main__':
    with open('admins_list.txt') as f:
        ConfigHolder.admin_ids = f.readlines()

    main = Main(TOKEN, Path('commands'), Path('last_stable_commands'))
    logger.info("Starting polling...")
    main.start()
