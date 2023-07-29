from __future__ import annotations

from dataclasses import dataclass
from os import getenv as getenv_optional
from typing import Optional

from app.common.config.utils import getenv, getenv_typed


@dataclass(kw_only=True)
class LDAPConfig:
    ldap_server: str
    ldap_port: int
    ldap_use_ssl: bool
    user: str
    password: str
    user_base: str
    ldap_request_domain: Optional[str]

    @staticmethod
    def from_env() -> LDAPConfig:
        return LDAPConfig(
            ldap_server=getenv("LDAP_SERVER"),
            ldap_port=getenv_typed("LDAP_PORT", int),
            ldap_use_ssl=getenv_typed("LDAP_USE_SSL", lambda x: x == 'True', False),
            user=getenv("LDAP_BIND_USER"),
            password=getenv("LDAP_BIND_PASSWORD"),
            user_base=getenv("LDAP_USER_BASE"),
            ldap_request_domain=getenv_optional("LDAP_REQUEST_DOMAIN"),
        )
