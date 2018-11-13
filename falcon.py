# Let's get this party started!
from __future__ import absolute_import
import falcon

class ThingsResource(object):
    def on_get(self, req, resp):
        """Handles GET requests"""
        resp.status = falcon.HTTP_200
        resp.body = 'Hello world!'

# falcon.API instances are callable WSGI apps
wsgi_app = api = falcon.API()

# Resources are represented by long-lived class instances
things = ThingsResource()

# things will handle all requests to the '/things' URL path
api.add_route('/hello', things)