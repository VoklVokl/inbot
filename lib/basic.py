from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List

from telegram import InputFile
from telegram.ext import Handler
from telegram.ext.handler import UT
from telegram.ext.utils.types import CCT


@dataclass
class HelpInfo:
    command_string: str
    description: str


class ExtHandler(Handler[UT, CCT], ABC):
    @abstractmethod
    def get_help_info(self) -> Optional[HelpInfo]:
        pass


@dataclass
class PageDescription:
    command: str
    short_text: str
    text: str
    photo: Optional[InputFile]


class ConfigHolder:
    admin_ids: List[str]
