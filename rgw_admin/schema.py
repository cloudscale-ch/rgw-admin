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
    def deserialize_from_python(cls, dct, report_unused=True):
        if not isinstance(dct, dict):
            raise fields.ValidationError(None, '%s is not a dictionary.' % dct)

        used = set()
        kwargs = {}
        for field in cls._fields:
            used.add(field.attribute or field.name)
            kwargs[field.name] = field.deserialize(dct)

        if report_unused:
            unused = set(dct) - used
            if unused:
                raise fields.ValidationError(
                    None, 'Found unused fields %s.' % ', '.join(unused)
                )

        return cls(**kwargs)

    @classmethod
    def as_field(cls, attribute=None):
        return fields.SchemaField(cls, attribute=None)

    def __repr__(self):
        fields = [
            "%s=%s" % (field.name, repr(getattr(self, field.name)))
            for field in self._fields
        ]
        return "%s(%s)" % (type(self).__name__, ', '.join(fields))
