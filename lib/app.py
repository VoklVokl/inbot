import distutils.dir_util
import os
import logging
import zipfile

from functools import partial
from pathlib import Path
from typing import Collection, List, Optional

from telegram import Update, Message
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

from lib.basic import ExtHandler, HelpInfo, PageDescription
from lib.commands.show_page import ShowPageCommand, process_hierarchy
from lib.utils import read_page_from_dir, send_message, subdirs

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


class Singleton(type):
    insts = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.insts:
            cls.insts[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls.insts[cls]


class App(metaclass=Singleton):
    def __init__(self, token, commands_dir: Path, stable_config_dir: Path, admin_ids: Collection[str]):
        self.commands_dir = commands_dir
        self.stable_config_dir = stable_config_dir
        self.updater = Updater(token, use_context=True)
        self.handlers: List[ExtHandler] = []
        self.admin_ids = set(admin_ids)
        self.is_active = True

    def add_handler(self, handler):
        self.updater.dispatcher.add_handler(handler)
        self.handlers.append(handler)

    def clear_handlers(self):
        for h in self.handlers:
            self.updater.dispatcher.remove_handler(h)

        self.handlers = []

    def start(self):
        load_commands(os.path.exists(self.stable_config_dir), None, None)
        logger.info("Done loading commands")

        logger.info("Starting polling...")
        self.updater.start_polling()


def load_commands(stable: bool, update: Optional[Update], context):
    if update is not None and update.message.from_user.username not in App().admin_ids:
        return

    if update is not None and update.message.effective_attachment is not None:
        logger.info("Received config file")
        attachment = update.message.effective_attachment
        if attachment.mime_type not in {'application/zip'}:
            send_message(update=update, text="Error, expected archive with commands")
            return

        path = update.message.effective_attachment.bot.get_file(attachment.file_id).download()
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(".")

    if stable and not os.path.isdir(App().stable_config_dir):
        raise Exception("Trying to load non-existing stable configuration.")

    logger.info("Clearing old handlers...")
    App().clear_handlers()
    logger.info("Done.")

    target_path = App().commands_dir if not stable else App().stable_config_dir

    on_load = update is None

    logger.info("Processing command dirs...")
    for subdir in subdirs(target_path):
        try:
            # TODO: add here custom command handlers living in dirs and use 'process hierarchy' only as fallback
            subdir_handlers = process_hierarchy(subdir, command_separator="_")
            for h in subdir_handlers:
                App().add_handler(h)
        except Exception as e:
            if not on_load:
                update.message.reply_text(
                    f"Error while trying to load new command configuration from dir {subdir.name}. "
                    "See logs for info. Will use previous stable configuration")

                logger.exception(f"Error while trying to load new command configuration from dir {subdir.name}. ")

                if not stable:
                    logger.info("Trying to load last stable command configuration...")
                    # load stable config
                    load_commands(True, update, context)
                    logger.info("Successfully loaded last stable command configuration.")
                    return

    logger.info("Done processing command dirs.")

    if update is not None:
        logger.info("Running commands to check their correctness...")
        for h in App().handlers:
            try:
                h.callback(update, context)
            except Exception as e:
                s = f"Error while trying to run command {h.command_string}. "
                update.message.reply_text(
                    s + " See logs for info. Will use previous stable configuration")
                logger.exception(s)
                load_commands(True, update, context)
                return
        logger.info("Done.")

    if not stable:
        logger.info("Saving new stable configuration...")
        distutils.dir_util.remove_tree(App().stable_config_dir.name)
        distutils.dir_util.copy_tree(App().commands_dir.name, App().stable_config_dir.name)
        logger.info("Done saving new stable configuration.")

    # We always have 'help' command
    help_page_description = read_page_from_dir(target_path, "help_message.md", "help_pic.jpg")

    help_handler = HelpCommand(help_page_description)
    App().add_handler(help_handler)
    App().add_handler(ReloadCommand())


class ReloadCommand(ExtHandler, CommandHandler):

    def __init__(self):
        super().__init__("reload", self.reload)
        App().updater.dispatcher.add_handler(MessageHandler(Filters.caption(update=['/reload']), partial(load_commands, False)))

    def reload(self, update: Update, context):
        load_commands(False, update, context)

    def is_visible_in_help(self, help_message: Message):
        return help_message.from_user.username in App().admin_ids

    def get_help_info(self) -> Optional[HelpInfo]:
        return HelpInfo(command_string="reload",
                        description="reload configuration from \'commands\' dir\. If message contains attach and it's caption is \'reload\',"
                                    "folder \'commands\' from archive will replace \'commands\' folder and then standard reload will happen")


class HelpCommand(ShowPageCommand):

    def __init__(self, help_page_description: PageDescription):
        super().__init__(help_page_description, [], [])

    def get_subcommands(self, update: Update, context: CallbackContext):
        return [h.get_help_info() for h in App().handlers if h.is_visible_in_help(update.message)]
