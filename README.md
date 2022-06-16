## Interactive novel bot

### Description ###

This bot was developed to help authors of interactive novels in Telegram to easily keep structured
objects like inventory/locations.

Configuration of commands is stored in `commands` folder.

Aside from `help_message.md` and `help_pic.jpg`, it contains subfolders each of them has the following format:
* descr.md -- description of command of the form `command_name<blank_line><blank_line>short_description<blank_line><blank_line>long_description` 
* pic.jpg -- optional picture for the page
* any number of subfolders of the same structure

Working example can be found in commands folder. 

Note that if we have top-level command with `command_name` "items" and nested command (corresponding to subfolder) with `command_name` "item1",
the string command for "item1" will actually be `/items_item1` (let's call it `full_command_name`).

When user enters a command, she will get response with long a description, picture (if any) and a list of subcommands if any (each subcommand is shown as pair of `full_command_name`, `short_description`).
List of subcommands is rendered at the place of service string `COMMANDSLIST` in `long_description`.
If no such string is present, list of subcommands will be rendered in the end of `long_description`.


When user enters `/help` command, she will see list of top-level commands (like "items" in our example)

There is a service command (for admin users only) `/reload` which will reload commands configuration on the fly. 
While reloading it will try to trigger all newly-loaded commands. If anything goes wrong, the bot will fallback to it's
previous stable configuration, which is saved in `last_stable_commands`.

Any text in descriptions should comply with these rules: https://core.telegram.org/bots/api#markdownv2-style , so you should escape characters like `.`, `!`, `)` with backslash in all cases they are not used as markdown symbols. 

### Running ###
`admins_list.txt` should contain list of admin users for this bot.

`token` should contain bot token (see there: https://core.telegram.org/bots#6-botfather).

You should create a conda environment:

`conda env create -f environment.yml`

Then activate it:

`conda activate inbot`

Then run bot:

`python3 main.py`
