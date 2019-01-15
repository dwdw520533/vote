'''
Lazy evaluated object. The function calls, __setitem__,
__setattr__ will be queued, and evaluated later when ._flush()
method is called.

Example
-------

    # Initiate a new lazy object
    lo = LazyObject()
    # queue methods
    lo.test(1, b=1)
    lo['x'] = 1
    lo.a = 5
    # bind with the actual object
    lo._set_obj(Test())
    # flush the queue
    lo._flush()

'''


class LazyRecord(object):
    '''
    Record of Lazy object.
    '''
    def __init__(self, name, queue):
        self._name = name
        self._queue = queue

    def __call__(self, *sub, **kw):
        self._queue.append([self._name, sub, kw])


class LazyObject(object):
    def __init__(self, obj=None):
        object.__setattr__(self, '__obj', obj)
        object.__setattr__(self, '__queue', [])

    def _flush(self):
        '''
        Run all the methods queued.
        '''
        for record in object.__getattribute__(self, '__queue'):
            name, sub, kw = record
            getattr(object.__getattribute__(self, '__obj'), name)(*sub, **kw)

    def _set_obj(self, obj):
        '''
        Set the actual object.
        '''
        object.__setattr__(self, '__obj', obj)

    def __getattr__(self, name):
        record = LazyRecord(name,
                            object.__getattribute__(self, '__queue'))
        return record

    def __setitem__(self, name, value):
        object.__getattribute__(self, '__queue')\
              .append(['__setitem__', (name, value), {}])

    def __delitem__(self, name):
        object.__getattribute__(self, '__queue')\
              .append(['__delitem__', (name,), {}])

    def __setattr__(self, name, value):
        object.__getattribute__(self, '__queue')\
              .append(['__setattr__', (name, value), {}])
