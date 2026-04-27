# confiddle

Hierarchical configuration for Python that's inspired by .NET and powered by Pydantic.

## What is it?

It's a hierarchical configuration loader that should be familiar to folks in [dotnet](https://learn.microsoft.com/en-us/dotnet/core/extensions/configuration)-land, but adapted for Python and leveraging Pydantic to build and validate the configuration data. Confiddle fiddles with the configuration so you don't have to!

Configurations can be loaded dynamically from a variety of sources:

- JSON configuration files (ex: `config.json`)
- Environment-specific JSON configuration files (ex: `config.dev.json` or `config.prod.json`)
- Environment variables
- [Argparse](https://docs.python.org/3/library/argparse.html)
- `**kwargs`

Those configurations are then merged together (shallowly, with later configurations overriding earlier ones), and used to build up the provided Pydantic model.

This is all customizable, too! With some easy tweaks, you can configure which configuration sources are loaded, what order they're loaded in, and the environment that your program is targeting. Confiddle will even bootstrap itself, so you can configure Confiddle's behavior the same way you'd load any other set of configurations.

## Installation

`pip install confiddle` (preferably inside your project's venv 🙂)

## Example

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
from confiddle import Confiddle, ConfiddleConfigModel, ConfigEnvironment, JsonConfigProviderConfigModel, EnvVarConfigProviderConfigModel
from app_config import AppConfig

confiddle = Confiddle(
    ConfiddleConfigModel(
        ## `directory_path="."` searches for config JSON files at the current working directory
        json_file=JsonConfigProviderConfigModel(directory_path="."),
        ## `prefix="MYAPP"` filters out any environment variable that doesn't have the "MYAPP" prefix
        env_var=EnvVarConfigProviderConfigModel(prefix="MYAPP"),
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

And that's it! Confiddle uses the configuration files and Pydantic models that you're already using, but formalizes the ingestion process, making all the magic happen in just a few lines of code.
