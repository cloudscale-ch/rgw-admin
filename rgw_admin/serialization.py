from rgw_admin.serialization import Schema
from rgw_admin import fields


class KeyEntry(Schema):
    user = fields.StringField()
    secret_key = fields.StringField()
    access_key = fields.StringField()


class User(Schema):
    email = fields.StringField()
    display_name = fields.StringField()
    user_id = fields.StringField()
    suspended = fields.IntegerField()
    max_buckets = fields.IntegerField(1000)
    tenant = fields.StringField()
    keys = fields.ListField(fields.KeyEntry)
    swift_keys = fields.AnyField()
    caps = fields.AnyField()
    subusers = fields.AnyField()
