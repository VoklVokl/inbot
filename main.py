import logging
from pathlib import Path

from lib.app import App

logging.basicConfig(filename='app.log', level=logging.INFO, filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    with open("token", mode="r") as f:
        TOKEN = f.readline()

    with open('admins_list.txt') as f:
        admin_ids = f.readlines()

    app = App(token=TOKEN,
              commands_dir=Path('commands'),
              stable_config_dir=Path('last_stable_commands'),
              admin_ids=admin_ids)

    logger.info("Starting...")
    app.start()
