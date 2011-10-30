import urllib

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        raise ImportError('simplejson required for python < 2.6')

import httplib2

from .. import harvest

JSON_MIME_TYPE = 'application/json'

class RestClient(httplib2.Http):
    headers = {
        'Accept': JSON_MIME_TYPE,
        'Content-Type': JSON_MIME_TYPE,
        'User-Agent': harvest.USER_AGENT,
        }

    def __init__(self, url_prefix, username, password, **kwargs):
        super(RestClient, self).__init__(**kwargs)

        # Handle 'subdomain' or 'subdomain.harvestapp.com' or full URL
        if not url_prefix.startswith('http'):
            if '.' not in url_prefix:
                url_prefix = '%s.harvestapp.com' % url_prefix
            url_prefix = 'https://%s' % url_prefix
        self.url_prefix = url_prefix

        self.add_credentials(username, password)

    def request(self, path, params=None, **kwargs):
        # Build URL
        url = self.url_prefix + path
        if params:
            url = '%s?%s' % (url, urllib.urlencode(params))

        # Add headers
        kwargs.setdefault('headers', {}).update(self.headers)

        try:
            response, content = super(RestClient, self).request(url, **kwargs)
        except Exception, e:
            raise harvest.HarvestError(e)

        # Success
        if response.status in [200, 201, 202, 304]:
            try:
                data = json.loads(content)
            except ValueError, e:
                raise HarvestError(e)

        # Error
        elif response.status == 401:
            raise harvest.HarvestAuthError(content)
        elif response.status == 503:
            raise harvest.HarvestThrottleLimit(
                content, response.get('retry-after'))
        else:
            raise harvest.HarvestError(content)
