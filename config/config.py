import logging
import os
from typing import Optional

import dotenv
import jinja2

from app.common.database import Database
from app.common.ldap import LDAP, LDAPConfig

from .utils import getenv, getenv_typed


class Config:
    production: bool
    log_directory: str
    log_file: str
    log_level: str
    web_listen_host: str
    web_listen_port: int
    web_thread_pool: int
    web_static_dir_root_path: str
    web_proxy_base: Optional[str]
    session_max_time: int
    database: Database
    database_migrations_path: str
    ldap_descriptor: LDAP
    jinja_env: jinja2.Environment

    @staticmethod
    def __load_dotenv():
        dotenv_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
        dotenv.load_dotenv(dotenv_path=dotenv_path, override=False)

    @staticmethod
    def load():
        Config.__load_dotenv()

        Config.production = getenv('AUTOMATION_ENVIRONMENT', 'development') == 'production'
        Config.log_directory = getenv('LOG_DIR')
        Config.log_file = getenv('LOG_FILE')
        Config.log_level = getenv('LOG_LEVEL', 'DEBUG')
        Config.web_listen_host = getenv('WEB_LISTEN_HOST')
        Config.web_listen_port = getenv_typed('WEB_LISTEN_PORT', int)
        Config.web_thread_pool = getenv_typed('WEB_THREAD_POOL_SIZE', int, 10)
        Config.web_static_dir_root_path = getenv('WEB_STATIC_DIR_ROOT_PATH')
        Config.session_max_time = getenv_typed('SESSION_MAX_TIME', int)
        Config.database = getenv_typed('DATABASE_PATH', Database)
        Config.database_migrations_path = getenv('DATABASE_MIGRATIONS_PATH')
        Config.ldap_descriptor = LDAP(LDAPConfig.from_env())
        Config.jinja_env = jinja2.Environment(loader=jinja2.PackageLoader('app.web', 'www'))
        Config.web_proxy_base = getenv('WEB_PROXY_BASE') if Config.production else None

        if not os.path.exists(Config.log_directory):
            os.mkdir(Config.log_directory)

    @staticmethod
    def setup_app_logger(log_file: Optional[str] = None):
        logger = logging.getLogger('app')
        logger.setLevel(Config.log_level)
        formatter = logging.Formatter(
            '[%(asctime)s] #%(thread)d [%(levelname)s] %(name)s: %(message)s', datefmt='%d/%b/%Y:%H:%M:%S')

        # create a StreamHandler to log to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(Config.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # create a FileHandler to log to a file
        file_handler = logging.FileHandler(os.path.join(Config.log_directory, log_file or Config.log_file))
        file_handler.setLevel(Config.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
