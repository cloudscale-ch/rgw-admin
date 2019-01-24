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
    sent_bytes = fields.IntegerField(attribute='bytes_sent')
    requests = fields.IntegerField(attribute='ops')
    successful_requests = fields.IntegerField(attribute='successful_ops')
    received_bytes = fields.IntegerField(attribute='bytes_received')


class BucketUsage(Schema):
    name = fields.StringField(attribute='bucket')
    datetime = fields.StringField(attribute='time')
    owner_id = fields.StringField(attribute='owner')
    timestamp = fields.IntegerField(attribute="epoch")
    categories = fields.ListField(Category)

    def get_requests(self):
        return sum(category.requests for category in self.categories)

    def get_successful_requests(self):
        return sum(category.successful_requests for category in self.categories)

    def get_sent_bytes(self):
        return sum(category.sent_bytes for category in self.categories)

    def get_received_bytes(self):
        return sum(category.received_bytes for category in self.categories)


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
    mtime = fields.StringField()
    max_marker = fields.StringField()

    @property
    def size_kb_actual(self):
        return sum(size.size_kb_actual for size in self.size.values())

    @property
    def size_kb(self):
        return sum(size.size_kb for size in self.size.values())

    @property
    def num_objects(self):
        return sum(size.num_objects for size in self.size.values())


BucketList = fields.ListField(Bucket)
KeyEntryList = fields.ListField(KeyEntry)
