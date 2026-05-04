# Argparse Provider and Configuration

Loads configuration from a parsed `argparse.Namespace` object or a plain dict. Typically passed to `load_config` at call time so that [argparse](https://docs.python.org/3/library/argparse.html) command line arguments can be loaded into the configuration.

**Flavor:** `ARGPARSE`

---

## Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `args` | `argparse.Namespace` or `dict` | `{}` | Parsed argparse Namespace or equivalent dict. |
| `scope` | `str` or `None` | `None` | Dot-separated key path to nest the data under before merging. |

### `args`

Accepts either an `argparse.Namespace` (the object returned by `parser.parse_args()`) or a plain `dict`. Namespace objects are converted to a dict via `vars()` automatically.

Fields whose value is `None` are filtered out before merging, so argparse defaults of `None` don't overwrite values from earlier providers.

### `scope`

When set, the args dict is nested at the given key path and merged deeply, preserving sibling keys. Without `scope`, the args are merged shallowly at the top level.

```python
# Without scope - top-level merge
ArgparseProviderConfig(args={"host": "cli-host"})
# -> {"host": "cli-host"}

# With scope - nested deep merge
ArgparseProviderConfig(args={"host": "cli-host"}, scope="database")
# -> {"database": {"host": "cli-host"}}
```

---

## Usage

```python
import argparse
from confiddle import ArgparseProviderConfig, ConfigFlavor

parser = argparse.ArgumentParser()
parser.add_argument("--host", default=None)
parser.add_argument("--port", type=int, default=None)
args = parser.parse_args()

confiddle = Confiddle(
    ConfiddleConfigModel(
        app=ProviderConfigModel(
            json_file_provider=JsonProviderConfig(directory_path=".")
        ),
        hierarchy=[ConfigFlavor.JSON, ConfigFlavor.ARGPARSE],
    )
)

config = confiddle.load_config(
    AppConfig,
    provider_configs=[ArgparseProviderConfig(args=args)],
)
```

---

## Notes

- `ARGPARSE` must appear in `hierarchy` for the provider to have any effect.
- Pass the provider via `provider_configs` on `load_config`, not via `ProviderConfigModel.argparse_provider`, unless the same args apply to every call which is unlikely.
- Use `default=None` on argparse arguments so that unset flags don't shadow values from lower-priority providers.
