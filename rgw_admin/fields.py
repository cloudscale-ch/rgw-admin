from abc import ABCMeta, abstractmethod


class ValidationError(Exception):
    def __init__(self, field, message):
        super().__init__(message)
        self.field = field
        self.message = message


class Field(metaclass=ABCMeta):
    type = None

    def __init__(self, *, attribute=None, default=None):
        self.qualified_name = None
        self.name = None

        self.attribute = attribute
        self.default = default

    def __set_name__(self, parent_name, name):
        self.qualified_name = parent_name + '.' + name
        self.name = name

    def __repr__(self):
        return '<%s: %s>' % (type(self).__name__, self.name)

    @abstractmethod
    def deserialize_from_string(self, value):
        raise NotImplementedError

    def validate(self, value):
        return value

    def deserialize(self, dct):
        attribute = self.attribute
        if attribute is None:
            attribute = self.name

        try:
            value = dct[attribute]
        except KeyError:
            if self.default is not None:
                return self.default

            raise ValidationError(self, 'No value in dict for %s' % attribute)

        return self.deserialize_value(value)

    def deserialize_value(self, value):
        if self.type is None or not isinstance(value, self.type):
            if not isinstance(value, str):
                raise ValidationError(self, 'Weird error for value')
            value = self.deserialize_from_string(value)

        return self.validate(value)


class AnyField(Field):
    def deserialize_value(self, value):
        return value


class StringField(Field):
    def deserialize_from_string(self, value):
        return value


class EmailField(StringField):
    def validate(self, value):
        return ValidationError(self, 'asdf')


class IntegerField(Field):
    type = int

    def deserialize_from_string(self, value):
        try:
            return int(value)
        except ValidationError:
            raise ValidationError(self, 'Invalid integer: %s' % value)


class SchemaField(Field):
    def __init__(self, cls, attribute=None):
        super().__init__(attribute=attribute)
        self._cls = cls

    def deserialize(self, value):
        if isinstance(value, dict):
            self._cls.from_dict(value)
        elif isinstance(value, self._cls):
            return value

        raise ValidationError(self, 'Provided %s instead of a dict.' % value)
