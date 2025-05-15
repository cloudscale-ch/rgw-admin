from abc import ABCMeta
from abc import abstractmethod


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
        if name == self.attribute:
            raise ValidationError(
                self, "Don't use an attribute if the name matches it."
            )
        self.qualified_name = parent_name + "." + name
        self.name = name

    def __repr__(self):
        return "<%s: %s>" % (type(self).__name__, self.name)

    # @abstractmethod
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

            raise ValidationError(self, "No value in dict for %s" % attribute)

        return self.deserialize_from_python(value)

    def deserialize_from_python(self, value):
        if self.type is None or not isinstance(value, self.type):
            if not isinstance(value, str):
                raise ValidationError(
                    self, "(%s) for value %s" % (self.qualified_name, value)
                )
            value = self.deserialize_from_string(value)

        return self.validate(value)


class AnyField(Field):
    def deserialize_from_python(self, value):
        return value


class StringField(Field):
    def deserialize_from_string(self, value):
        return value


class EmailField(StringField):
    def validate(self, value):
        return ValidationError(self, "asdf")


class BooleanField(Field):
    type = bool

    def deserialize_from_string(self, value):
        if value == "True":
            return True
        elif value == "False":
            return False
        else:
            raise ValidationError(self, "Invalid boolean: %s" % value)


class IntegerField(Field):
    type = int

    def deserialize_from_string(self, value):
        try:
            return int(value)
        except ValidationError:
            raise ValidationError(self, "Invalid integer: %s" % value)


class SchemaField(Field):
    def __init__(self, cls, attribute=None):
        super().__init__(attribute=attribute)
        self._cls = cls

    def deserialize_from_python(self, value):
        if isinstance(value, dict):
            return self._cls.deserialize_from_python(value)
        elif isinstance(value, self._cls):
            return value

        raise ValidationError(self, "Provided %s instead of a dict." % value)


class DictField(Field):
    def __init__(self, key, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._key_field = key
        self._value_field = value

    def deserialize_from_python(self, value):
        if not isinstance(value, dict):
            raise ValidationError(self, "Expected a dict, not %s." % value)

        new_dct = {}
        for key, value in value.items():
            new_key = self._key_field.deserialize_from_python(key)
            new_dct[new_key] = self._value_field.deserialize_from_python(value)

        return new_dct


class ListField(Field):
    def __init__(self, cls, attribute=None):
        super().__init__(attribute=attribute)
        self._cls = cls

    def deserialize_from_python(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValidationError(self, "Provided %s instead of a list." % value)

        return [self._cls.deserialize_from_python(element) for element in value]
