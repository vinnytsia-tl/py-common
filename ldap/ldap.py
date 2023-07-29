import logging
from typing import Any, Optional

import ldap3

from .config import LDAPConfig
from .user import User

logger = logging.getLogger(__name__)


ATTRS = ['userPrincipalName', 'displayName', 'distinguishedName']


class LDAPException(Exception):
    pass


class LDAPBindException(LDAPException):
    pass


class LDAPSearchException(LDAPException):
    pass


class LDAP():
    def __init__(self, config: LDAPConfig):
        self.config = config
        self.server = ldap3.Server(config.ldap_server, config.ldap_port, use_ssl=config.ldap_use_ssl)

    def __get_connection(self, read_only: bool = True) -> ldap3.Connection:
        connection = ldap3.Connection(self.server, user=self.config.user, password=self.config.password,
                                      read_only=read_only, version=3)
        if not connection.bind():
            logger.error('LDAP bind failed with user %s', self.config.user)
            raise LDAPBindException
        return connection

    def __build_user(self, entry: Any) -> User:
        if entry is None or entry.userPrincipalName.value is None or \
           entry.displayName.value is None or entry.distinguishedName.value is None:
            logger.warning('LDAP entry is invalid')
            raise LDAPSearchException
        return User(entry.userPrincipalName.value, entry.displayName.value, entry.distinguishedName.value)

    def set_password(self, username: str, new_password: str) -> bool:
        conn = self.__get_connection()
        user = self.get_user(username)
        return conn.extend.microsoft.modify_password(user.distinguished_name, new_password)

    def get_users(self, search_base: Optional[str] = None) -> list[User]:
        if search_base is None:
            search_base = self.config.user_base

        conn = self.__get_connection()
        search_filter = '(&(objectCategory=person)(objectClass=user))'

        if not conn.search(search_base, search_filter, attributes=ATTRS):
            logger.error('No LDAP entries found for search base %s and filter %s', search_base, search_filter)
            return []

        entries = conn.entries
        logger.info('Found %d LDAP entries for search base %s and filter %s', len(entries), search_base, search_filter)
        return [self.__build_user(entry) for entry in entries]

    def get_user(self, user_principal_name: str, search_base: Optional[str] = None) -> User:
        if search_base is None:
            search_base = self.config.user_base

        conn = self.__get_connection()
        user_principal_name = self.normalize_login(user_principal_name)
        search_filter = f'(&(objectCategory=person)(objectClass=user)(userPrincipalName={user_principal_name}))'
        if not conn.search(search_base, search_filter, attributes=ATTRS):
            logger.error('No LDAP entries found for search base %s and filter %s', search_base, search_filter)
            raise LDAPSearchException

        entry = conn.entries[0]
        if entry is not None:
            logger.info('Found LDAP entry for search base %s and filter %s', search_base, search_filter)
            return self.__build_user(entry)

        logger.warning('No LDAP entry found for user %s in search base %s', user_principal_name, search_base)
        raise LDAPSearchException

    def login(self, username: str, password: str) -> bool:
        if username == '' or password == '':
            logger.warning('LDAP login without username/password is unsupported')
            return False

        username = self.normalize_login(username)
        conn = ldap3.Connection(self.server, user=username, password=password)
        if not conn.bind():
            logger.warning("LDAP bind failed with user %s", username)
            return False

        return True

    def normalize_login(self, login: str) -> str:
        return login if '@' in login else f"{login}@{self.config.ldap_request_domain}"
