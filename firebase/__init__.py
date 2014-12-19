import requests
import urlparse #for urlparse and urljoin
import os #for os.path.dirname
import json #for dumps
import datetime #for parse datetime object to string
import decimal #for parse decimal to string

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return total_seconds(obj)
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self, obj)

class Firebase():
    ROOT_URL = '' #no trailing slash
    auth_token = None

    def __init__(self, root_url, auth_token=None):
        self.ROOT_URL = root_url.rstrip('/')
        self.auth_token = auth_token

    #These methods are intended to mimic Firebase API calls.

    def child(self, path):
        root_url = '%s/' % self.ROOT_URL
        url = urlparse.urljoin(root_url, str(path).lstrip('/'))
        return Firebase(url, auth_token=self.auth_token)

    def parent(self):
        url = os.path.dirname(self.ROOT_URL)
        #If url is the root of your Firebase, return None
        up = urlparse.urlparse(url)
        if up.path == '':
            return None #maybe throw exception here?
        return Firebase(url, auth_token=self.auth_token)

    def name(self):
        return os.path.basename(self.ROOT_URL)

    def toString(self):
        return self.__str__()
    def __str__(self):
        return self.ROOT_URL

    def set(self, value):
        return self.put(value)

    def push(self, data):
        return self.post(data)

    def update(self, data):
        return self.patch(data)

    def remove(self):
        return self.delete()

    
    #These mirror REST API functionality

    def put(self, data):
        return self.__request('put', data = data)

    def patch(self, data):
        return self.__request('patch', data = data)

    def get(self):
        return self.__request('get')

    #POST differs from PUT in that it is equivalent to doing a 'push()' in
    #Firebase where a new child location with unique name is generated and
    #returned
    def post(self, data):
        return self.__request('post', data = data)

    def delete(self):
        return self.__request('delete')


    #Private

    def __request(self, method, **kwargs):
        #Firebase API does not accept form-encoded PUT/POST data. It needs to
        #be JSON encoded.
        if 'data' in kwargs:
            kwargs['data'] = json.dumps(kwargs['data'], cls=JSONEncoder)

        params = {}
        if self.auth_token:
            if 'params' in kwargs:
                params = kwargs['params']
                del kwargs['params']
            params.update({'auth': self.auth_token})

        r = requests.request(method, self.__url(), params=params, **kwargs)
        r.raise_for_status() #throw exception if error
        return r.json()


    def __url(self):
        #We append .json to end of ROOT_URL for REST API.
        return '%s.json' % self.ROOT_URL

# TODO: Make caching persistent
_GlobalCache = {}

class CachedFirebase(Firebase):
    ROOT_URL = '' #no trailing slash
    auth_token = None

    def __init__(self, root_url, auth_token=None):
        self.ROOT_URL = root_url.rstrip('/')
        self.auth_token = auth_token

    #These methods are intended to mimic Firebase API calls.

    def child(self, path):
        root_url = '%s/' % self.ROOT_URL
        url = urlparse.urljoin(root_url, str(path).lstrip('/'))
        return CachedFirebase(url, auth_token=self.auth_token)

    def parent(self):
        url = os.path.dirname(self.ROOT_URL)
        #If url is the root of your Firebase, return None
        up = urlparse.urlparse(url)
        if up.path == '':
            return None #maybe throw exception here?
        return CachedFirebase(url, auth_token=self.auth_token)

    def name(self):
        return os.path.basename(self.ROOT_URL)

    def toString(self):
        return self.__str__()
    def __str__(self):
        return self.ROOT_URL

    def set(self, value):
        return self.put(value)

    def push(self, data):
        return self.post(data)

    def update(self, data):
        return self.patch(data)

    def remove(self):
        return self.delete()

    #These mirror REST API functionality

    def put(self, data):
        global _GlobalCache
        _GlobalCache[self.ROOT_URL] = None
        return self.__request('put', data = data)

    def patch(self, data):
        global _GlobalCache
        _GlobalCache[self.ROOT_URL] = None
        return self.__request('patch', data = data)

    def get(self):
        global _GlobalCache
        if not self.ROOT_URL in _GlobalCache:
            _GlobalCache[self.ROOT_URL] = self.__request('get')
        return _GlobalCache[self.ROOT_URL]

    #POST differs from PUT in that it is equivalent to doing a 'push()' in
    #Firebase where a new child location with unique name is generated and
    #returned
    def post(self, data):
        global _GlobalCache
        _GlobalCache[self.ROOT_URL] = None
        return self.__request('post', data = data)

    def delete(self):
        global _GlobalCache
        _GlobalCache[self.ROOT_URL] = None
        return self.__request('delete')

    #Private

    def __request(self, method, **kwargs):
        #Firebase API does not accept form-encoded PUT/POST data. It needs to
        #be JSON encoded.
        if 'data' in kwargs:
            kwargs['data'] = json.dumps(kwargs['data'], cls=JSONEncoder)

        params = {}
        if self.auth_token:
            if 'params' in kwargs:
                params = kwargs['params']
                del kwargs['params']
            params.update({'auth': self.auth_token})

        r = requests.request(method, self.__url(), params=params, **kwargs)
        r.raise_for_status() #throw exception if error
        return r.json()


    def __url(self):
        #We append .json to end of ROOT_URL for REST API.
        return '%s.json' % self.ROOT_URL
