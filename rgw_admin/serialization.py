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


class Category(Schema):
    category = fields.StringField()
    bytes_sent = fields.IntegerField()
    ops = fields.IntegerField()
    successful_ops = fields.IntegerField()
    bytes_received = fields.IntegerField()


class Bucket(Schema):
    name = fields.StringField(attribute='bucket')
    time = fields.StringField()
    owner_id = fields.StringField(attribute='owner')
    timestamp = fields.IntegerField(attribute="epoch")
    categories = fields.ListField(Category)


class Entry(Schema):
    user = fields.StringField()
    buckets = fields.ListField(Bucket)


class Usage(Schema):
    entries = fields.ListField(Entry)
