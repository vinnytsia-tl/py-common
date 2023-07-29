import logging

import cherrypy

from app.config import Config

from .utils import init_hooks

init_hooks()
logger = logging.getLogger(__name__)


def get_cherrypy_config():
    return {
        '/': {
            'tools.secureheaders.on': True,
            'tools.sessions.on': True,
            'tools.sessions.httponly': True,
            'tools.staticdir.root': Config.web_static_dir_root_path,
            'tools.trailing_slash.on': False,
            'tools.response_headers.on': True,
            'tools.sessions.secure': Config.production,
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static',
        },
        '/.well-known': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static/.well-known',
        },
    }


class Web:
    @staticmethod
    def start(root: object):
        logger.info('Starting web server...')

        cherrypy.config.update({
            'server.socket_host': Config.web_listen_host,
            'server.socket_port': Config.web_listen_port,
            'server.thread_pool': Config.web_thread_pool,
            'engine.autoreload.on': not Config.production,
            'engine.autoreload.frequency': 1,
            'log.screen': not Config.production,
            'log.screen.level': Config.log_level,
            'log.error_file': Config.log_directory + '/web_error.log',
            'log.access_file': Config.log_directory + '/web_access.log',
            'tools.proxy.on': Config.web_proxy_base is not None,
            'tools.proxy.base': Config.web_proxy_base,
        })
        logger.debug('Web server config updated.')

        cherrypy.engine.subscribe('start', Config.database.cleanup)
        logger.debug('Web engine subscribed.')
        cherrypy.tree.mount(root, '/', get_cherrypy_config())
        logger.debug('Web tree mounted.')
        cherrypy.engine.start()
        logger.info('Web server started.')
        cherrypy.engine.block()

    @staticmethod
    def stop():
        cherrypy.engine.exit()

    @staticmethod
    @cherrypy.tools.register('before_finalize', priority=60)
    def secureheaders():
        logger.debug('Execute secureheaders hook')

        headers = cherrypy.response.headers
        headers['X-Frame-Options'] = 'DENY'
        headers['X-XSS-Protection'] = '1; mode=block'
        if Config.production:
            headers['Content-Security-Policy'] = '''
                default-src 'self' https;
                font-src 'self' data: fonts.gstatic.com;
                style-src 'self' fonts.googleapis.com;
                img-src 'self' data:;
            '''
