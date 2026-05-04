# EnvVarProviderConfig

Loads configuration from environment variables. Supports a prefix filter and a configurable delimiter for mapping nested keys.

**Flavor:** `ENV_VAR`

---

## Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `prefix` | `str` or `None` | `None` | Only env vars that start with this prefix are loaded. The prefix itself is consumed (stripped) before mapping to config keys. |
| `delimiter` | `str` | `:` | Separates key segments within an env var name. Used to build nested dicts. |

### `prefix`

When set, only env vars whose name starts with `<prefix>` are considered. The prefix and leading delimiter are stripped before the remaining name is matched to config fields.

```shell
# With prefix="APP" and delimiter=":"
APP:HOST=myhost    ->  {"host": "myhost"}
APP:PORT=9000      ->  {"port": "9000"}
OTHER:KEY=ignored  ->  (filtered out)
```

When `None`, all environment variables are loaded, though this isn't recommended most of the time.

### `delimiter`

Controls how env var names are split into nested key paths.

```shell
# With prefix="APP" and delimiter=":"
APP:DATABASE:HOST=db.local  ->  {"database": {"host": "db.local"}}

# With prefix="APP" and delimiter="__"
APP__DATABASE__HOST=db.local  ->  {"database": {"host": "db.local"}}
```

Key segments are lowercased before matching against model fields.

---

## Usage

```python
from confiddle import EnvVarProviderConfig

# Filter by prefix, use default ":" delimiter
EnvVarProviderConfig(prefix="MYAPP")

# Custom delimiter
EnvVarProviderConfig(prefix="MYAPP", delimiter="__")

# No prefix - loads all env vars (use with caution)
EnvVarProviderConfig()
```

---

## Mapping env vars to model fields

Given this model:

```python
class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080

class Config(BaseModel):
    app: AppConfig = AppConfig()
    debug: bool = False
```

And these env vars (prefix `"SVC"`, delimiter `":"`):

```shell
SVC:APP:HOST=myhost
SVC:APP:PORT=9000
SVC:DEBUG=true
```

The provider produces:

```python
{
    "app": {"host": "myhost", "port": "9000"},
    "debug": "true"
}
```

Pydantic handles type coercion when the model is built.

---

## Multiple env var providers

Register several `EnvVarProviderConfig` instances to merge from different prefixes:

```python
ProviderConfigModel(
    env_var_provider=[
        EnvVarProviderConfig(prefix="APP"),
        EnvVarProviderConfig(prefix="SVC"),
    ]
)
```

---

## Notes

- Env var values are always strings. Pydantic coerces them to the correct type when building the model.
- Key segments are lowercased. `APP:HOST` and `app:host` map to the same field.
- The provider is stateless. It reads `os.environ` at load time.
