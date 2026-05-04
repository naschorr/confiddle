# Confiddle Documentation

Hierarchical configuration for Python, inspired by .NET and powered by Pydantic.

---

## Overview

Confiddle loads configuration from multiple sources, merges them in a defined order, and validates the result against a Pydantic model. Later sources in the hierarchy win over earlier ones.

```
JSON base configuration file -> JSON environmental configuration file -> env vars -> argparse -> click -> dict
```

The merge is **shallow**: if two sources both supply the same top-level key, the later one replaces it entirely. Sub-keys from the earlier source that the later one omits are lost unless a `scope` is used (see [DictProviderConfig](providers/dict.md), [ArgparseProviderConfig](providers/argparse.md), and [ClickProviderConfig](providers/click.md)).

---

## Installation

```
pip install confiddle
```

---

## Quick Start

A web service that layers three configuration sources - base JSON defaults, a production-specific JSON override, and a runtime environment variable.

```jsonc
// config.json - shared across all environments
{
    "app_name": "my-web-service",
    "workers": 4,
    "admin_username": "admin"
}
```

```jsonc
// config.dev.json - local development overrides
{
    "host": "localhost",
    "port": 8080,
    "debug": true
}
```

```jsonc
// config.prod.json - production overrides
{
    "host": "1.2.3.4",
    "port": 80,
    "debug": false
}
```

```shell
## Injected by the platform's secrets manager
export MYAPP:ADMIN_PASSWORD="hunter2"
```

```python
## app_config.py
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    app_name: str
    workers: int
    host: str
    port: int
    debug: bool
    admin_username: str
    admin_password: str = Field(default="", exclude=True)
```

```python
## main.py
from confiddle import (
    Confiddle,
    ConfiddleConfigModel,
    ProviderConfigModel,
    ConfigEnvironment,
    JsonProviderConfig,
    EnvVarProviderConfig,
)
from app_config import AppConfig

confiddle = Confiddle(
    ConfiddleConfigModel(
        app=ProviderConfigModel(
            ## `directory_path="."` searches for config JSON files at the current working directory
            json_file_provider=JsonProviderConfig(directory_path="."),
            ## `prefix="MYAPP"` filters out any environment variable that doesn't have the "MYAPP" prefix
            env_var_provider=EnvVarProviderConfig(prefix="MYAPP"),
        ),
        ## This tells it to only load production configurations, like config.prod.json above.
        ## Note that it'll still load the base configurations regardless, like config.json above.
        environment=ConfigEnvironment.PROD,
    )
)

config = confiddle.load_config(AppConfig)

## State of `config` after loading:
## config.app_name       -> "my-web-service"  (from config.json)
## config.workers        -> 4                 (from config.json)
## config.admin_username -> "admin"           (from config.json)
## config.host           -> "1.2.3.4"         (from config.prod.json)
## config.port           -> 80                (from config.prod.json)
## config.debug          -> False             (from config.prod.json)
## config.admin_password -> "hunter2"         (from MYAPP:ADMIN_PASSWORD env var)
```

---

## API

### `Confiddle`

The main entry point.

```python
Confiddle(confiddle_config: ConfiddleConfigModel | None = None)
```

| Parameter | Type | Description |
|---|---|---|
| `confiddle_config` | `ConfiddleConfigModel` or `None` | Configuration for Confiddle itself. When `None`, Confiddle bootstraps from `CONFIDDLE_*` env vars and `confiddle.json` in the working directory. |

#### `load_config`

```python
confiddle.load_config(config_model, *, provider_configs=[])
```

| Parameter | Type | Description |
|---|---|---|
| `config_model` | `type[T]` | The Pydantic model to build. |
| `provider_configs` | `Sequence[BaseProviderConfig]` | Additional providers to merge at call time (e.g. argparse args, per-request dicts). |

Returns an instance of `config_model`.

---

### `ConfiddleConfigModel`

Controls how Confiddle itself is configured.

```python
ConfiddleConfigModel(
    app=ProviderConfigModel(...),
    environment=ConfigEnvironment.DEV,
    hierarchy=[ConfigFlavor.JSON, ConfigFlavor.JSON_ENV, ConfigFlavor.ENV_VAR, ...],
)
```

| Field | Type | Default | Description |
|---|---|---|---|
| `app` | `ProviderConfigModel` | empty | Provider configs for your application config. |
| `environment` | `ConfigEnvironment` | `DEV` | Active environment, used to select env-specific JSON files. |
| `hierarchy` | `list[ConfigFlavor]` | `[JSON, JSON_ENV, ENV_VAR, ARGPARSE, DICT]` | Merge order. Later entries win. |
| `bootstrap` | `ProviderConfigModel` | `CONFIDDLE` env vars + `confiddle.json` | How Confiddle loads its own config. Rarely set manually. |

---

### `ProviderConfigModel`

Registers provider configs for an app (or for bootstrap).

```python
ProviderConfigModel(
    json_file_provider=JsonProviderConfig(...),      # single provider
    env_var_provider=EnvVarProviderConfig(...),
    argparse_provider=ArgparseProviderConfig(...),
    click_provider=ClickProviderConfig(...),
    dict_provider=[DictProviderConfig(...), DictProviderConfig(...),]   # list of providers
)
```

Every field accepts a single config object or a list. Multiple providers of the same type are each applied in order.

---

### `ConfigEnvironment`

```python
from confiddle import ConfigEnvironment

ConfigEnvironment.DEV   # "dev"
ConfigEnvironment.TEST  # "test"
ConfigEnvironment.PROD  # "prod"
```

Controls which environment-specific JSON file is loaded (e.g. `config.dev.json`).

---

### `ConfigFlavor`

```python
from confiddle import ConfigFlavor

ConfigFlavor.JSON       # base JSON file  (config.json)
ConfigFlavor.JSON_ENV   # env JSON file   (config.dev.json)
ConfigFlavor.ENV_VAR    # environment variables
ConfigFlavor.ARGPARSE   # argparse Namespace
ConfigFlavor.CLICK      # Click context / kwargs
ConfigFlavor.DICT       # plain dict
```

Used to build `hierarchy` in `ConfiddleConfigModel`.

---

## Providers

Each provider is a `BaseProviderConfig` subclass that tells Confiddle where to read configuration data from. See the individual provider docs for full field reference.

| Provider | Config class | Flavor | Doc |
|---|---|---|---|
| JSON (base configuration file) | `JsonProviderConfig` | `JSON` | [providers/json.md](providers/json.md) |
| JSON (environmental configuration file) | `JsonProviderConfig` | `JSON_ENV` | [providers/json.md](providers/json.md) |
| Environment variables | `EnvVarProviderConfig` | `ENV_VAR` | [providers/env_var.md](providers/env_var.md) |
| Argparse | `ArgparseProviderConfig` | `ARGPARSE` | [providers/argparse.md](providers/argparse.md) |
| Click | `ClickProviderConfig` | `CLICK` | [providers/click.md](providers/click.md) |
| Dict | `DictProviderConfig` | `DICT` | [providers/dict.md](providers/dict.md) |

A single `JsonProviderConfig` automatically participates in both the `JSON` and `JSON_ENV` flavors - Confiddle splits it internally based on whether an environment is active.

---

## Hierarchy and merge order

The `hierarchy` list in `ConfiddleConfigModel` controls the merge order. Confiddle processes providers left-to-right and merges shallowly, so the last provider to supply a key wins.

```python
# ENV_VAR overrides JSON; DICT overrides both
hierarchy=[ConfigFlavor.JSON, ConfigFlavor.JSON_ENV, ConfigFlavor.ENV_VAR, ConfigFlavor.DICT]
```

To flip priorities, reorder the list:

```python
# JSON wins over everything which can be useful for locked-down deployments
hierarchy=[ConfigFlavor.ENV_VAR, ConfigFlavor.JSON]
```

Flavors absent from `hierarchy` are ignored entirely, even if providers are registered for them.

---

## Environments

Set `environment` in `ConfiddleConfigModel` to control which env-specific JSON file is loaded alongside the base file.

```
config.json       <- always loaded (JSON flavor)
config.dev.json   <- loaded when environment=DEV (JSON_ENV flavor)
config.prod.json  <- loaded when environment=PROD (JSON_ENV flavor)
```

The filename template defaults to `config.{environment}.json` and is configurable per `JsonProviderConfig`. See [providers/json.md](providers/json.md).

---

## Bootstrapping

Confiddle bootstraps itself before loading your app config. By default it reads from:

- `CONFIDDLE:*` environment variables
- `confiddle.json` in the working directory

This means you can configure Confiddle's own `environment` and `hierarchy` from outside the code, without touching Python. Override the bootstrap behavior by setting providers inside `ConfiddleConfigModel.bootstrap` explicitly.

---

## Warnings

Confiddle emits a `UserWarning` when a `JsonProviderConfig` was registered with an active environment but neither the base file nor the env-specific file returned any data. This typically means the `directory_path` or `filename_template` is wrong.

```
UserWarning: JsonProvider was configured but did not resolve any data across 2 flavors.
```
