from rgw_admin.schema import Schema
from rgw_admin import fields


class KeyEntry(Schema):
    user = fields.StringField()
    secret_key = fields.StringField()
    access_key = fields.StringField()


class User(Schema):
    display_name = fields.StringField()
    user_id = fields.StringField()
    email = fields.StringField()
    keys = fields.ListField(KeyEntry)
    suspended = fields.IntegerField()
    max_buckets = fields.IntegerField()
    tenant = fields.StringField()
    swift_keys = fields.AnyField()
    caps = fields.AnyField()
    subusers = fields.AnyField()
