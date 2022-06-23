from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from telegram import InputFile, Message
from telegram.ext import Handler
from telegram.ext.handler import UT
from telegram.ext.utils.types import CCT


@dataclass
class HelpInfo:
    command_string: str
    description: str


class ExtHandler(Handler[UT, CCT], ABC):

    def is_visible_in_help(self, help_message: Message):
        return True

    @abstractmethod
    def get_help_info(self) -> Optional[HelpInfo]:
        pass


@dataclass
class PageDescription:
    command: str
    short_text: str
    text: str
    photo: Optional[InputFile]
