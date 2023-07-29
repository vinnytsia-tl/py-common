from __future__ import annotations

import time
import logging

import cherrypy

from app.config import Config
from app.models import UserRole

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


def get_current_role():
    cursor = Config.database.execute('''
        SELECT role FROM users
        INNER JOIN sessions ON users.login = sessions.username
        WHERE session_id = ?
    ''', (cherrypy.session.id,))
    res = cursor.fetchone() or (0,)
    return UserRole(res[0])


def authorize(role: UserRole = UserRole.COMMON):
    current_role = get_current_role()
    if current_role.value < role.value:
        logger.debug('User is not authorized (role is %s, required %s), redirecting to /home', current_role, role)
        raise cherrypy.HTTPRedirect("/home")
    cherrypy.session['current_role'] = current_role


def init_hooks():
    cherrypy.tools.authenticate = cherrypy.Tool('before_handler', authenticate)
    cherrypy.tools.authorize = cherrypy.Tool('before_handler', authorize)
