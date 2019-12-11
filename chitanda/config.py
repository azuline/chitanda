import json
import logging
import sys

from chitanda import CONFIG_DIR

logger = logging.getLogger(__name__)

CONFIG_PATH = CONFIG_DIR / 'config.json'

BLANK_CONFIG = {
    'trigger_character': '.',
    'user_agent': 'chitanda bot',
    'irc_servers': {},
    'discord_token': '',
    'webserver': {'enable': False, 'port': 38428},
    'modules': {
        'global': [
            'aliases',
            'choose',
            'help',
            'irc_channels',
            'reload',
            'sed',
            'urbandictionary',
            'wolframalpha',
        ]
    },
    'aliases': {
        'global': {
            'c': 'choose',
            'urban': 'urbandictionary',
            'wa': 'wolframalpha',
        }
    },
    'admins': {},
}


class Config:
    def __init__(self):
        self._config = None  # Lazy load config.

    def reload(self):
        self._config = self._load_config()

    def __getitem__(self, key):
        if self._config is None:
            self._config = self._load_config()

        return self._config[key]

    def _load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r') as cf:
                try:
                    return json.load(cf)
                except json.decoder.JSONDecodeError:
                    pass

        logger.critical('Config is not valid JSON or does not exist.')
        sys.exit(1)


config = Config()
