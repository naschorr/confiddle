# Confiddle Examples

---

## 1. Basic JSON config

Load a single JSON file from the current directory.

```jsonc
// config.json
{
    "host": "0.0.0.0",
    "port": 9000
}
```

```python
from pydantic import BaseModel
from confiddle import Confiddle, ConfiddleConfigModel, ProviderConfigModel, JsonProviderConfig

class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080
    debug: bool = False

confiddle = Confiddle(
    ConfiddleConfigModel(
        app=ProviderConfigModel(
            json_file_provider=JsonProviderConfig(directory_path=".")
        )
    )
)

config = confiddle.load_config(AppConfig)
# config.host  -> "0.0.0.0"
# config.port  -> 9000
# config.debug -> False  (model default, not in file)
```

---

## 2. Environment-specific JSON overrides

Layer a base file with an environment-specific override. The env file only needs to contain the keys it overrides.

```jsonc
// config.json
{
    "host": "localhost",
    "port": 80,
    "debug": true,
    "workers": 1
}
```

```jsonc
// config.prod.json
{
    "host": "0.0.0.0",
    "debug": false,
    "workers": 8
}
```

```python
from pydantic import BaseModel
from confiddle import Confiddle, ConfiddleConfigModel, ProviderConfigModel, JsonProviderConfig, ConfigEnvironment, ConfigFlavor

class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    workers: int = 1


confiddle = Confiddle(
    ConfiddleConfigModel(
        app=ProviderConfigModel(
            json_file_provider=JsonProviderConfig(directory_path=".")
        ),
        environment=ConfigEnvironment.PROD,
        hierarchy=[ConfigFlavor.JSON, ConfigFlavor.JSON_ENV],
    )
)

config = confiddle.load_config(AppConfig)
# config.host    -> "0.0.0.0"    (from config.prod.json)
# config.port    -> 80           (from config.json)
# config.debug   -> False        (from config.prod.json)
# config.workers -> 8            (from config.prod.json)
```

---

## 3. Environment variables override JSON

Secrets and deployment-time values injected via env vars, base defaults from JSON.

```jsonc
// config.json
{
    "host": "localhost",
    "port": 8080
}
```

```shell
## environment variables
export MYAPP:DB_PASSWORD=hunter2
export MYAPP:PORT=443
```

```python
from pydantic import BaseModel
from confiddle import Confiddle, ConfiddleConfigModel, ProviderConfigModel, JsonProviderConfig, EnvVarProviderConfig, ConfigFlavor

class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080
    db_password: str = ""

confiddle = Confiddle(
    ConfiddleConfigModel(
        app=ProviderConfigModel(
            json_file_provider=JsonProviderConfig(directory_path="."),
            env_var_provider=EnvVarProviderConfig(prefix="MYAPP"),
        ),
        hierarchy=[ConfigFlavor.JSON, ConfigFlavor.ENV_VAR],
    )
)

config = confiddle.load_config(AppConfig)
# config.host        -> "localhost"   (from config.json)
# config.port        -> 443           (from env vars)
# config.db_password -> "hunter2"     (from env vars)
```

---

## 4. Argparse integration

Pass argparse's `Namespace` or `vars()`'s `dict` output and have them ingested into the configuration.

```python
import argparse
from pydantic import BaseModel
from confiddle import Confiddle, ConfiddleConfigModel, ProviderConfigModel, JsonProviderConfig, ArgparseProviderConfig, ConfigFlavor

class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080

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

## 5. Click integration

Pass Click's `Context` or `**kwargs` output and have them ingested into the configuration.

```python
import click
from pydantic import BaseModel
from confiddle import Confiddle, ConfiddleConfigModel, ProviderConfigModel, JsonProviderConfig, ClickProviderConfig, ConfigFlavor

class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080

@click.command()
@click.option("--host", default=None)
@click.option("--port", type=int, default=None)
def run(**kwargs):
    confiddle = Confiddle(
        ConfiddleConfigModel(
            app=ProviderConfigModel(
                json_file_provider=JsonProviderConfig(directory_path=".")
            ),
            hierarchy=[ConfigFlavor.JSON, ConfigFlavor.CLICK],
        )
    )
    config = confiddle.load_config(
        AppConfig,
        provider_configs=[ClickProviderConfig(args=kwargs)],
    )
    print(config)
```

---

## 6. Dict provider for testing and defaults

Inject arbitrary dictionary values programmatically, which is useful in tests or for computed defaults.

```python
from pydantic import BaseModel
from confiddle import Confiddle, ConfiddleConfigModel, ConfigFlavor, DictProviderConfig

class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080

confiddle = Confiddle(
    ConfiddleConfigModel(hierarchy=[ConfigFlavor.JSON, ConfigFlavor.DICT])
)

config = confiddle.load_config(
    AppConfig,
    provider_configs=[DictProviderConfig(data={"host": "test-host", "port": 1234})],
)
```

---

## 7. Scoped dict provider for nested models

Use `scope` to target a specific section of a nested config model. Scoped providers deep-merge, so only the keys you supply are overridden.

```python
from pydantic import BaseModel
from confiddle import Confiddle, ConfiddleConfigModel, ConfigFlavor, DictProviderConfig

class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "mydb"

class AppConfig(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    debug: bool = False

confiddle = Confiddle(
    ConfiddleConfigModel(hierarchy=[ConfigFlavor.DICT])
)

config = confiddle.load_config(
    AppConfig,
    provider_configs=[
        DictProviderConfig(data={"host": "__db_host__", "port": 5433}, scope="database"),
    ],
)
# config.database.host -> "__db_host__"
# config.database.port -> 5433
# config.database.name -> "mydb"  (default preserved - not overwritten)
# config.debug         -> False   (unrelated key untouched)
```

---

## 8. Multiple providers of the same type

Any provider type can be registered multiple times. They are applied in list order within their flavor, so later entries win on conflict.

```python
from confiddle import Confiddle, ConfiddleConfigModel, ProviderConfigModel, JsonProviderConfig, EnvVarProviderConfig, ConfigFlavor

confiddle = Confiddle(
    ConfiddleConfigModel(
        app=ProviderConfigModel(
            json_file_provider=[
                JsonProviderConfig(directory_path="/etc/myapp"),     # system-wide defaults
                JsonProviderConfig(directory_path="./config"),       # local overrides
            ],
            env_var_provider=[
                EnvVarProviderConfig(prefix="APP"),                  # primary app vars
                EnvVarProviderConfig(prefix="SECRETS"),              # secrets manager vars
            ],
        ),
        hierarchy=[ConfigFlavor.JSON, ConfigFlavor.JSON_ENV, ConfigFlavor.ENV_VAR],
    )
)
```

All four providers participate: both JSON directories are read for base and env files, then both env var prefixes are merged in. A key present in `SECRETS:*` will override the same key from `APP:*`.

---

## 9. Full production setup

Base configuration JSON + environment configuration JSON override + env var secrets, driven by environment.

Confiddle bootstraps itself from `CONFIDDLE:*` env vars and `confiddle.json`, so `environment` doesn't need to be read manually, just set `CONFIDDLE:ENVIRONMENT=prod` in the deployment environment and Confiddle picks it up automatically.

```shell
## environment variables
export CONFIDDLE:ENVIRONMENT=prod
export APP:DB_PASSWORD=hunter2
```

```python
from confiddle import (
    Confiddle, ConfiddleConfigModel, ProviderConfigModel,
    JsonProviderConfig, EnvVarProviderConfig,
    ConfigFlavor,
)
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    host: str = "localhost"
    port: int = 8080
    debug: bool = False
    workers: int = 1
    db_password: str = Field(default="", exclude=True)

# environment is set via CONFIDDLE:ENVIRONMENT env var at deploy time
confiddle = Confiddle(
    ConfiddleConfigModel(
        app=ProviderConfigModel(
            json_file_provider=JsonProviderConfig(directory_path="./config"),
            env_var_provider=EnvVarProviderConfig(prefix="APP"),
        ),
        hierarchy=[
            ConfigFlavor.JSON,
            ConfigFlavor.JSON_ENV,
            ConfigFlavor.ENV_VAR,
        ],
    )
)

config = confiddle.load_config(AppConfig)
```

Files expected:

```
config/
    config.json         # shared defaults
    config.dev.json     # dev overrides
    config.prod.json    # prod overrides
```
