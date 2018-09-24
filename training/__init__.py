# -*- coding: utf-8

import json
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import SignedCookieSessionFactory

from pyramid.config import Configurator
from pluralize import pluralize
from .views import default

session_factory = SignedCookieSessionFactory('9272374112', timeout=10800)
authn_policy = AuthTktAuthenticationPolicy( 'secret')
authz_policy = ACLAuthorizationPolicy()



def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.set_session_factory(session_factory)
    config.include('pyramid_tm')
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.include('pyramid_jinja2')
    config.commit()
    jinja2_env = config.get_jinja2_environment()
    jinja2_env.filters['pluralize'] = pluralize
    jinja2_env.globals.update(generatetree = default.generatetree)
    config.include('.models')
    config.include('.routes')
    config.scan()
    return config.make_wsgi_app()
