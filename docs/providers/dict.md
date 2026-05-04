# DictProviderConfig

Loads configuration from a plain Python dict. Useful for computed values, programmatic overrides, and really any situation where you'd like to inject a dictionary of data.

**Flavor:** `DICT`

---

## Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `data` | `dict` | `{}` | Configuration values to merge. |
| `scope` | `str` or `None` | `None` | Dot-separated key path to nest the data under before merging. |

### `data`

Any dict. Keys are matched against the target model's fields. Unknown keys are ignored (Pydantic's default behavior).

### `scope`

When set, `data` is nested at the given dot-separated path and merged **deeply** with whatever is already present at that location. Sibling keys at the same level that `data` does not mention are preserved.

Without `scope`, the merge is **shallow**: if `data` supplies a key that another provider already set, the entire value at that key is replaced.

```python
# Shallow (no scope) - replaces the entire "database" dict
DictProviderConfig(data={"database": {"host": "new-host"}})
# After merge: database.port, database.name etc. revert to model defaults

# Deep (with scope) - only "host" is overwritten inside "database"
DictProviderConfig(data={"host": "new-host"}, scope="database")
# After merge: database.port and database.name are preserved from earlier providers
```

---

## Usage

```python
from confiddle import DictProviderConfig, ConfigFlavor

confiddle = Confiddle(
    ConfiddleConfigModel(
        hierarchy=[ConfigFlavor.JSON, ConfigFlavor.DICT]
    )
)

# Top-level override
config = confiddle.load_config(
    AppConfig,
    provider_configs=[DictProviderConfig(data={"host": "override", "port": 9999})],
)

# Scoped override targeting a nested section
config = confiddle.load_config(
    FullConfig,
    provider_configs=[DictProviderConfig(data={"host": "__db_host__", "port": 5433}, scope="database")],
)
```

---

## Multiple scoped providers

Multiple scoped providers targeting the same key are deep-merged in order:

```python
provider_configs=[
    DictProviderConfig(data={"host": "db-host"}, scope="database"),
    DictProviderConfig(data={"port": 5433}, scope="database"),
]
# Result: {"database": {"host": "db-host", "port": 5433, ...defaults...}}
```

---

## Notes

- `DICT` must appear in `hierarchy` for the provider to have any effect.
- The dict provider is the simplest way to inject test data or computed values without touching files or env vars.
- When registered via `ProviderConfigModel.dict_provider`, the same data applies to every `load_config` call. Use `provider_configs` on `load_config` for call-specific overrides.
