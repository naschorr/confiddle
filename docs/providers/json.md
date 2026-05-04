# JsonProviderConfig

Loads configuration from JSON files on disk. A single `JsonProviderConfig` participates in two flavors automatically:

- `JSON` - loads the base file (e.g. `config.json`)
- `JSON_ENV` - loads the environment-specific file (e.g. `config.dev.json`)

Both files are optional. A missing file is silently skipped and returns no data.

---

## Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `directory_path` | `str` or `Path` | required | Directory to search for config files. |
| `filename_template` | `str` | `config.{environment}.json` | Filename pattern. May include `{environment}` as a placeholder. |

### `directory_path`

Path to the directory that contains the JSON files. Accepts a string or `Path` object. The directory must exist at the time the provider config is created.

### `filename_template`

Controls which files are loaded.

- If the template contains `{environment}`, Confiddle derives two filenames:
  - Base configuration file: placeholder stripped, double periods collapsed (`config.{environment}.json` -> `config.json`)
  - Environment configuration file: placeholder substituted (`config.{environment}.json` + `DEV` -> `config.dev.json`)
- If the template has no `{environment}` placeholder, the substitution is a no-op and `JSON_ENV` loads the same filename as `JSON`. Consider omitting `JSON_ENV` from `hierarchy` in this case.

---

## Usage

```python
from confiddle import JsonProviderConfig

# Default - looks for config.json and config.<env>.json
JsonProviderConfig(directory_path="./config")

# Custom template
JsonProviderConfig(
    directory_path="./config",
    filename_template="settings.{environment}.json",
)

# Fixed filename - same file regardless of environment
JsonProviderConfig(
    directory_path="./config",
    filename_template="app-settings.json",
)
```

---

## How the two flavors work

Given `environment=ConfigEnvironment.PROD` and the default template:

| Flavor | File loaded |
|---|---|
| `JSON` | `config.json` |
| `JSON_ENV` | `config.prod.json` |

Both must appear in `hierarchy` for both to be applied:

```python
from confiddle import ConfigFlavor

hierarchy=[ConfigFlavor.JSON, ConfigFlavor.JSON_ENV]
# JSON loads first, JSON_ENV overrides it
```

Omitting a flavor from `hierarchy` prevents that file from being read:

```python
hierarchy=[ConfigFlavor.JSON]
# Only config.json is read; config.prod.json is ignored
```

---

## Multiple JSON providers

Register several `JsonProviderConfig` instances to load from multiple directories. They are applied in list order within each flavor - later entries win on conflict.

```python
from confiddle import ProviderConfigModel

ProviderConfigModel(
    json_file_provider=[
        JsonProviderConfig(directory_path="/etc/myapp"),   # base defaults
        JsonProviderConfig(directory_path="./config"),     # local overrides
    ]
)
```

---

## Notes

- Files are always optional. Confiddle emits a `UserWarning` only when a provider with an active environment returns no data from *either* the base or env file - this usually means the path or template is wrong.
- The `environment` field exists on the model for internal framework use. Do not set it manually; Confiddle stamps it via `_inject_context` based on `ConfiddleConfigModel.environment`.
