import click
import pytest
from click.testing import CliRunner
from pydantic import BaseModel, ValidationError

from confiddle.config.enums.config_flavor import ConfigFlavor
from confiddle.config.enums.merge_strategy import MergeStrategy
from confiddle.config.models.providers.click_provider_config import ClickProviderConfig
from confiddle.config.providers.click_provider import ClickProvider


class SampleModel(BaseModel):
    name: str = "default"
    value: int = 0


## ── ClickProviderConfig ───────────────────────────────────────────────────────


class TestArgsCoercion:
    def test_accepts_plain_dict(self):
        config = ClickProviderConfig(args={"name": "hello"})
        assert config.args == {"name": "hello"}

    def test_accepts_click_context(self):
        @click.command()
        @click.option("--name", default="from-ctx")
        @click.pass_context
        def cmd(ctx, name):
            pass

        runner = CliRunner()
        captured: list[click.Context] = []

        @click.command()
        @click.option("--name", default="from-ctx")
        @click.pass_context
        def cmd_capture(ctx, name):
            captured.append(ctx)

        runner.invoke(cmd_capture, [])
        ctx = captured[0]
        config = ClickProviderConfig(args=ctx)
        assert config.args == {"name": "from-ctx"}

    def test_accepts_object_with_params_attribute(self):
        class FakeContext:
            params = {"name": "duck-typed"}

        config = ClickProviderConfig(args=FakeContext())
        assert config.args == {"name": "duck-typed"}

    def test_invalid_type_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ClickProviderConfig(args=42)

    def test_empty_dict_default(self):
        config = ClickProviderConfig()
        assert config.args == {}


class TestConfigFlavor:
    def test_config_flavor_is_click(self):
        config = ClickProviderConfig(args={})
        assert config.config_flavor is ConfigFlavor.CLICK


## ── ClickProvider ────────────────────────────────────────────────────────────


class TestClickProvider:
    def test_returns_data_from_dict(self):
        provider = ClickProvider(SampleModel, ClickProviderConfig(args={"name": "x"}))
        assert provider.get_config() == {"name": "x"}

    def test_none_values_stripped(self):
        # Click uses None as "option not supplied" - these must not reach the model
        provider = ClickProvider(SampleModel, ClickProviderConfig(args={"name": "x", "value": None}))
        assert provider.get_config() == {"name": "x"}

    def test_all_none_produces_empty_dict(self):
        provider = ClickProvider(SampleModel, ClickProviderConfig(args={"name": None, "value": None}))
        assert provider.get_config() == {}

    def test_is_shallow_merge_without_scope(self):
        provider = ClickProvider(SampleModel, ClickProviderConfig(args={"name": "x"}))
        assert provider.merge_strategy is MergeStrategy.SHALLOW

    def test_loads_from_real_click_invocation(self):
        captured: list[dict] = []

        @click.command()
        @click.option("--name", default=None)
        @click.option("--value", type=int, default=None)
        def cmd(name, value):
            captured.append({"name": name, "value": value})

        runner = CliRunner()
        runner.invoke(cmd, ["--name", "cli-name", "--value", "42"])

        provider = ClickProvider(SampleModel, ClickProviderConfig(args=captured[0]))
        assert provider.get_config() == {"name": "cli-name", "value": 42}

    def test_loads_from_click_context(self):
        captured: list[click.Context] = []

        @click.command()
        @click.option("--name", default=None)
        @click.pass_context
        def cmd(ctx, name):
            captured.append(ctx)

        runner = CliRunner()
        runner.invoke(cmd, ["--name", "ctx-name"])

        provider = ClickProvider(SampleModel, ClickProviderConfig(args=captured[0]))
        assert provider.get_config() == {"name": "ctx-name"}

    def test_unrecognised_keys_filtered_out(self):
        # DictProvider filters keys against the model schema - unknown keys are dropped
        provider = ClickProvider(SampleModel, ClickProviderConfig(args={"name": "x", "extra": "ignored"}))
        result = provider.get_config()
        assert result["name"] == "x"
        assert "extra" not in result
