from lib.basic import HelpInfo, PageDescription
from lib.commands.show_page import ShowPageCommand


class HelpCommand(ShowPageCommand):

    def __init__(self, help_page_description: PageDescription):
        super().__init__(help_page_description, [], [])

    def add_help_info(self, help_info: HelpInfo):
        self.subcommands.append(help_info)
