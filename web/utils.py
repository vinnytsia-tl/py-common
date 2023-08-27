from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlencode

import cherrypy

from app.config import Config

logger = logging.getLogger(__name__)


def is_authenticated():
    agent = cherrypy.request.headers.get('User-Agent')
    session_time = time.time() - Config.session_max_time
    exe_str = "SELECT 1 FROM sessions WHERE session_id = ? AND agent = ? AND time > ?;"
    cursor = Config.database.execute(exe_str, (cherrypy.session.id, agent, session_time))
    return cursor.fetchone() is not None


def authenticate():
    if not is_authenticated():
        logger.debug('User is not authenticated, redirecting to /auth')
        raise cherrypy.HTTPRedirect("/auth")


def init_hooks():
    cherrypy.tools.authenticate = cherrypy.Tool('before_handler', authenticate)


def save_session(username: str):
    with Config.database.get_connection() as connection:
        cursor = connection.cursor()
        agent = cherrypy.request.headers.get('User-Agent')
        session_time = time.time()
        exe_str = "DELETE FROM sessions WHERE username = ? OR session_id = ?;"
        cursor.execute(exe_str, (username, cherrypy.session.id))
        exe_str = "INSERT INTO sessions(session_id, username, agent, time) values(?, ?, ?, ?);"
        cursor.execute(exe_str, (cherrypy.session.id, username, agent, session_time))


def to_query_string(args: dict[str, Any]) -> str:
    return urlencode({k: v for k, v in args.items() if v is not None and v != ''})
