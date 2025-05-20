# rgw-admin - Python API for Ceph Objects Gateway

This library is currently used by [cloudscale.ch](https://www.cloudscale.ch/en) to
access the
[admin API of the Ceph Objects Gateway](https://docs.ceph.com/en/latest/radosgw/adminops/)
(also called *RADOS Gateway* or *RGW*). It's not feature complete.

## Development

### Setup

The project uses [pre-commit](https://pre-commit.com) to run source code formatters and
type checking before commit. A Makefile target is provided to create a virtualenv ready
for development:

```shell
pre-commit install
make venv
. venv/bin/activate
```

### Tests

Unit test can be run using [pytest](https://docs.pytest.org/en/stable/):

```bash
pytest
```

### Type Checking

Type checking can be run using [mypy](https://github.com/python/mypy):

```bash
mypy
```
