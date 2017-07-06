import collections

from rgw_admin import fields


class SchemaMeta(type):
    @classmethod
    def __prepare__(self, name, bases):
        return collections.OrderedDict()

    def __new__(self, name, bases, class_dict):
        class_dict['_fields'] = ordered = []
        for key, value in list(class_dict.items()):
            if isinstance(value, fields.Field):
                del class_dict[key]

                value.__set_name__('', key)
                ordered.append(value)

        return type.__new__(self, name, bases, class_dict)


class Schema(metaclass=SchemaMeta):
    def __init__(self, *args, **kwargs):
        for field, arg in zip(self._fields, args):
            if field.name in kwargs:
                raise TypeError(
                    "%s got multiple values for keyword argument '%s'"
                    % (type(self).__name__, field.name)
                )
            kwargs[field.name] = arg

        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def from_dict(cls, dct):
        used = set()
        kwargs = {}
        for field in cls._fields:
            used.add(field.name)
            kwargs[field.name] = field.deserialize(dct)

        return cls(**kwargs)

    @classmethod
    def as_field(cls):
        return fields.from_dict(cls)

    def __repr__(self):
        fields = [
            "%s=%s" % (field.name, repr(getattr(self, field.name)))
            for field in self._fields
        ]
        return "%s(%s)" % (type(self).__name__, ', '.join(fields))
