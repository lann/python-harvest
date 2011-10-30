from client import rest
import items

__author__ = 'Lann Martin'
__copyright__ = 'Copyright 2011 %s' % __author__
__credits__ = [__author__]
__license__ = 'MIT'
__version__ = '0.1'
__maintainer__ = __author__
__email__ = 'python-harvest@lannbox.com'

USER_AGENT = 'python-harvest %s' % __version__

class Harvest(object):
    def __init__(self, *args, **kwargs):
        client_cls = kwargs.pop('client_cls', rest.RestClient)
        self.client = client_cls(*args, **kwargs)
        self.request = self.client.request

        for cls in ['Client', 'Project', 'Entry', 'Task', 'User',
                    'ExpenseCategory', 'Expense', 'Invoice']:
            setattr(self, cls, getattr(items, cls)._bind(self))

        self.Day = items.Day._bind(self, _methods=['for_date'])

class HarvestError(Exception):
    pass

class HarvestAuthError(HarvestError):
    pass

class HarvestThrottleLimit(HarvestError):
    def __init__(self, msg, retry_after=None):
        self.retry_after = retry_after
        super(HarvestThrottleLimit, self).__init__(msg)
