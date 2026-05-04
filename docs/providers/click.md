# Click Provider and Configuration

Loads configuration from a [Click](https://click.palletsprojects.com/en/stable/) command's arguments. Accepts either the `**kwargs` dict received by a Click command function or a `click.Context` object.

**Flavor:** `CLICK`

---

## Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `args` | `dict` or `click.Context` | `{}` | Click kwargs dict or a `click.Context` whose `.params` will be used. |
| `scope` | `str` or `None` | `None` | Dot-separated key path to nest the data under before merging. |

### `args`

Accepts:

- A plain `dict` - typically the `**kwargs` received by a Click command function
- A `click.Context` object - `.params` is extracted automatically

### `scope`

When set, the args dict is nested at the given key path and merged deeply, preserving sibling keys. Without `scope`, the args are merged shallowly at the top level.

---

## Usage

### From `**kwargs`

```python
import click
from confiddle import Confiddle, ConfiddleConfigModel, ClickProviderConfig, ConfigFlavor

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
```

### From a `click.Context`

```python
@click.command()
@click.option("--host", default=None)
@click.pass_context
def run(ctx):
    config = confiddle.load_config(
        AppConfig,
        provider_configs=[ClickProviderConfig(args=ctx)],
    )
```

---

## Notes

- `CLICK` must appear in `hierarchy` for the provider to have any effect.
- Click option values of `None` are filtered out automatically. Set `default=None` on options you want to be optional so they don't shadow values from lower-priority providers.
- Click is not a required dependency of confiddle. The duck-typing on `.params` means you can use this provider without adding Click to your `dependencies`.
