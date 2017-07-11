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
    name = fields.StringField(attribute='category')
    bytes_sent = fields.IntegerField()
    ops = fields.IntegerField()
    successful_ops = fields.IntegerField()
    bytes_received = fields.IntegerField()


class BucketUsage(Schema):
    name = fields.StringField(attribute='bucket')
    datetime = fields.StringField(attribute='time')
    owner_id = fields.StringField(attribute='owner')
    timestamp = fields.IntegerField(attribute="epoch")
    categories = fields.ListField(Category)


class UsageEntry(Schema):
    user_id = fields.StringField(attribute='user')
    buckets = fields.ListField(BucketUsage)


class Usage(Schema):
    entries = fields.ListField(UsageEntry)


class BucketSize(Schema):
    size_kb_actual = fields.IntegerField()
    size_kb = fields.IntegerField()
    num_objects = fields.IntegerField()


class Bucket(Schema):
    name = fields.StringField(attribute='bucket')
    index_pool = fields.StringField()
    owner = fields.StringField()
    size = fields.DictField(
        key=fields.StringField(),
        value=BucketSize,
        attribute='usage'
    )
    marker = fields.StringField()
    id = fields.StringField()
    master_ver = fields.StringField()
    bucket_quota = fields.AnyField()
    ver = fields.StringField()
    pool = fields.StringField()
    mtime = fields.StringField()
    max_marker = fields.StringField()


BucketList = fields.ListField(Bucket)
