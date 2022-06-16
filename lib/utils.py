from pathlib import Path
from typing import Optional, List

from telegram import Update, InputFile

from lib.basic import PageDescription


def flatten(xss):
    return [x for xs in xss for x in xs]


def send_message(update: Update, text, photo: Optional[InputFile]):
    if photo is not None:
        update.message.reply_photo(photo=photo,
                                   caption=text,
                                   parse_mode='MarkdownV2')
    else:
        update.message.reply_markdown_v2(text)


def read_page_from_dir(page_dir_path: Path, descr_name="descr.md", image_name="pic.jpg") -> PageDescription:
    with open(page_dir_path.joinpath(descr_name), mode='r') as f:
        lines = f.readlines()
        text = "".join(lines)

        parts = text.split("\n\n\n")
        assert len(
            parts) == 3, f"Error in {page_dir_path}. Description file should be of format " \
                         f"command<newline><newline>short description<newline><newline>text. "

        photo = None
        photo_path = page_dir_path.joinpath(image_name)
        if photo_path.is_file():
            with open(photo_path, mode='rb') as f:
                photo = f.read()

        return PageDescription(
            command=parts[0],
            short_text=parts[1],
            text=parts[2],
            photo=InputFile(photo) if photo is not None else None
        )


def render_list(lst: List[str], ordered=False):
    unordered_bullet = '•'
    return "\n".join([f"{str((i + 1)) + '.' if ordered else unordered_bullet}{item}" for i, item in enumerate(lst)])


def subdirs(path: Path):
    for f in path.iterdir():
        if f.is_dir():
            yield f