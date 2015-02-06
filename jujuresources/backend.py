import hashlib
import os
from urllib import urlretrieve
from urlparse import urlparse, urljoin


class ALL(object):
    pass


class ResourceContainer(dict):
    def __init__(self, output_dir):
        super(ResourceContainer, self).__init__()
        self._required = set()
        self.output_dir = output_dir

    def add_required(self, name, resource):
        self[name] = Resource.get(name, resource, self.output_dir)
        self._required.add(name)

    def add_optional(self, name, resource):
        self[name] = Resource.get(name, resource, self.output_dir)

    def all(self):
        return self.values()

    def required(self):
        return [self[name] for name in self._required]

    def subset(self, which):
        if not which:
            return self.required()
        if which is ALL:
            return self.all()
        if not isinstance(which, list):
            return [self[which]]
        return [self[name] for name in which]


class Resource(object):
    """
    Base class for a Resource.

    Handles local file resources (with explicit ``filename`` or ``destination``).
    """
    @classmethod
    def get(cls, name, definition, output_dir):
        """
        Dispatch to the right subclass based on the definition.
        """
        if 'url' in definition:
            return URLResource(name, definition, output_dir)
        elif 'pip' in definition:
            return PIPResource(name, definition, output_dir)
        else:
            return Resource(name, definition, output_dir)

    def __init__(self, name, definition, output_dir):
        self.name = name
        self.filename = definition.get('filename', '')
        self.destination = definition.get(
            'destination', os.path.join(output_dir, self.filename))
        self.hash = definition.get('hash', '')
        self.hash_type = definition.get('hash_type', '')
        self.output_dir = output_dir

    def fetch(self, mirror_url=None):
        return

    def verify(self):
        if not os.path.isfile(self.destination):
            return False
        with open(self.destination) as fp:
            hash = hashlib.new(self.hash_type)
            hash.update(fp.read())
            if self.hash != hash.hexdigest():
                return False
        return True


class URLResource(Resource):
    def __init__(self, name, definition, output_dir):
        super(URLResource, self).__init__(name, definition, output_dir)
        self.url = definition.get('url', '')
        self.filename = definition.get(
            'filename', os.path.basename(urlparse(self.url).path))
        self.destination = definition.get(
            'destination', os.path.join(self.output_dir, self.filename))

    def fetch(self, mirror_url=None):
        if mirror_url:
            url = urljoin(mirror_url, self.filename)
        else:
            url = self.url
        if url.startswith('./'):
            url = url[2:]  # urlretrieve complains about this for some reason
        if not os.path.exists(os.path.dirname(self.destination)):
            os.makedirs(os.path.dirname(self.destination))
        try:
            urlretrieve(url, self.destination)
        except IOError:
            pass  # ignore download errors; they will be caught by verify


class PIPResource(Resource):
    def __init__(self, name, definition, output_dir):
        raise NotImplementedError('PIP resources are not yet supported')

    def fetch(self, mirror_url=None):
        raise NotImplementedError('PIP resources are not yet supported')
