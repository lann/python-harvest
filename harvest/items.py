import datetime
import functools

def harvest_datetime(value):
    if isinstance(value, basestring):
        value = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
    return value

def harvest_time(value):
    #TODO handle 12-hour format
    if isinstance(value, basestring):
        value = datetime.datetime.strptime(value, '%H:%M').time()
    return value

def harvest_date(value):
    if isinstance(value, basestring):
        value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
    return value

def harvest_date_alt(value):
    if isinstance(value, basestring):
        _,
        value = datetime.datetime.strptime(value, '%Y-%m-%d').date()
    return value

COMMON_TYPES = {
        'created_at': harvest_datetime,
        'updated_at': harvest_datetime,
        }

class Item(object):
    item_name = None
    get_path = None
    all_path = None

    hyphenated_attrs = []
    attr_types = COMMON_TYPES

    def __init__(self, data, _harvest=None):
        self._harvest = _harvest

        if data:
            item_name = self.item_name or self.__class__.__name__.lower()
            data = data.get(item_name, data)

        self.data = data or {}

    def __getattr__(self, name):
        try:
            value = self.data[name]
        except KeyError:
            raise AttributeError(name)

        attr_type = self.types.get(name)

        if issubclass(attr_type, Item):
            attr_type = attr_type._bind(self._harvest)

        if not attr_type:
            return value
        elif isinstance(value, list):
            return map(attr_type, value)
        else:
            return attr_type(value)

    _bind_methods = ['get', 'all']
    @classmethod
    def _bind(cls, harvest, _methods=_bind_methods):
        bound = functools.partial(cls, _harvest=harvest)
        bound.__name__ += cls.__name__

        for name in _methods or []:
            setattr(bound, name,
                    functools.partial(getattr(cls, name), harvest))

        return bound

    @classmethod
    def _fetch(cls, harvest, path, **params):
        data = harvest.request(path, params)
        if isinstance(data, list):
            return map(cls._bind(harvest, _methods=None), data)
        else:
            return cls(data, _harvest=harvest)

    @classmethod
    def get(cls, harvest, item_id):
        if not cls.get_path:
            raise NotImplementedError

        if '%' in cls.get_path:
            path = cls.get_path % item_id
        else:
            path = cls.get_path + str(item_id)
        return cls._fetch(harvest, path)

    @classmethod
    def all(cls, harvest, **params):
        if not cls.all_path:
            raise NotImplementedError

        return cls._fetch(harvest, cls.all_path, **params)

class ChildItem(Item):
    child_path = None

    @classmethod
    def _contribute_getters(cls, parent_cls, singular=None, plural=None):
        def _get(self, child_id):
            return cls.get(self._harvest, self.id, child_id)
        _get.__name__ = 'get_%s' % (
            singular or parent_cls.item_name or parent_cls.__name__.lower())
        setattr(parent_cls, _get.__name__, _get)

        def _all(self, **params):
            return cls.all(self._harvest, self.id, **params)
        _all.__name__ = 'get_%s' % (plural or _get.__name__ + 's')
        setattr(parent_cls, _all.__name__, _all)

    @classmethod
    def get(cls, harvest, parent_id, item_id):
        if not cls.child_path:
            raise NotImplementedError

        path = cls.child_path % (parent_id, item_id)
        return cls._fetch(harvest, path)

    @classmethod
    def all(cls, harvest, parent_id, **params):
        if not cls.child_path:
            raise NotImplementedError

        path = cls.child_path % (parent_id, '')
        return cls._fetch(harvest, path, **params)


# http://www.getharvest.com/api/clients
class Client(Item):
    get_path = '/clients/'
    all_path = get_path

    def get_contacts(self):
        return ClientContact.for_client(self._harvest, self.id)

    def get_projects(self):
        return Project.for_client(self._harvest, self.id)

# http://www.getharvest.com/api/client-contacts
class ClientContact(Item):
    item_name = 'contact'
    get_path = '/contacts/'
    all_path = get_path

    @classmethod
    def for_client(cls, harvest, client_id):
        return map(cls._bind(harvest, _methods=None),
                   harvest.request('/clients/%s/contacts' % client_id))

# http://www.getharvest.com/api/projects
class Project(Item):
    get_path = '/projects/'
    all_path = get_path

    attr_types = dict(
        COMMON_TYPES,
        earliest_record_at=harvest_date,
        latest_record_at=harvest_date,
        )

    @classmethod
    def for_client(cls, harvest, client_id):
        return cls.all(harvest, client=client_id)

# http://www.getharvest.com/api/time-tracking
class Entry(Item):
    item_name = 'day_entry'
    get_path = '/daily/show/'

    attr_types = dict(
        COMMON_TYPES,
        started_at=harvest_time,
        ended_at=harvest_time,
        )

class Day(Item):
    item_name = 'daily'
    attr_types = dict(
        day_entries=Entry,
        projects=Project,
        for_day=harvest_date,
        )

    @classmethod
    def for_date(cls, harvest, day=None, year=None):
        if isinstance(day, int):
            # day of year and year
            if year:
                year = int(year)

            elif day > 0:
                raise ValueError('cannot use day > 0 without year')

            # days before today
            else:
                day = datetime.date.today() - datetime.timedelta(days=day)

        # date-like object
        if hasattr(day, 'strftime'):
            day, year = map(int, day.strftime('%j %Y').split())

        if day:
            data = harvest.request('/daily/%d/%d' % (day, year))
        else:
            data = harvest.request('/daily')

        return cls(data, _harvest=harvest)

# http://www.getharvest.com/api/tasks
class Task(Item):
    get_path = '/tasks/'
    all_path = get_path

# http://www.getharvest.com/api/people
class User(Item):
    get_path = '/people/'
    all_path = get_path

# http://www.getharvest.com/api/expenses
class ExpenseCategory(Item):
    item_name = 'expense_category'
    get_path = '/expense_categories/'
    all_path = get_path

# http://www.getharvest.com/api/expense-tracking
class Expense(Item):
    get_path = '/expenses/'
    all_path = get_path

    attr_types = dict(
        COMMON_TYPES,
        spent_at=harvest_date,
        )

# http://www.getharvest.com/api/user-assignment
class UserAssignment(ChildItem):
    item_name = 'user_assignment'
    child_path = '/projects/%s/user_assignments/%s'

    def get_project(self):
        return Project.get(self._harvest, self.project_id)

    def get_user(self):
        return User.get(self._harvest, self.user_id)

UserAssignment._contribute_getters(Project)

# http://www.getharvest.com/api/task-assignment
class TaskAssignment(ChildItem):
    item_name = 'task_assignment'
    child_path = '/projects/%s/task_assignments/%s'

    def get_project(self):
        return Project.get(self._harvest, self.project_id)

    def get_task(self):
        return Task.get(self._harvest, self.task_id)

TaskAssignment._contribute_getters(Project)

# http://www.getharvest.com/api/invoices
class Invoice(Item):
    item_name = 'doc'
    get_path = '/invoices/'
    all_path = get_path

    attr_types = dict(
        COMMON_TYPES,
        due_at=harvest_date,
        issued_at=harvest_date,
        )

# http://www.getharvest.com/api/invoice-messages
class InvoiceMessage(ChildItem):
    item_name = 'message'
    child_path = '/invoices/%s/messages/%s'

InvoiceMessage._contribute_getters(Invoice)

# http://www.getharvest.com/api/invoice-payments
class InvoicePayment(ChildItem):
    item_name = 'payment'
    child_path = '/invoices/%s/payments/%s'

    attr_types = dict(
        COMMON_TYPES,
        paid_at=harvest_datetime,
        )

InvoicePayment._contribute_getters(Invoice)

# http://www.getharvest.com/api/invoice-categories
class InvoiceCategory(Item):
    item_name = 'category'
    all_path = '/invoice_item_categories'
