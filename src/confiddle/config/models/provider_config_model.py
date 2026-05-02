from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, BeforeValidator, Field

from confiddle.config.models.providers.argparse_provider_config import ArgparseProviderConfig
from confiddle.config.models.providers.click_provider_config import ClickProviderConfig
from confiddle.config.models.providers.dict_provider_config import DictProviderConfig
from confiddle.config.models.providers.env_var_provider_config import EnvVarProviderConfig
from confiddle.config.models.providers.json_provider_config import JsonProviderConfig
from confiddle.helpers.field_validator import FieldValidator

_wrap_in_list = lambda v: [v]

_ArgparseProviders = Annotated[
    list[ArgparseProviderConfig], BeforeValidator(FieldValidator.coerce(list, transform=_wrap_in_list))
]
_ClickProviders = Annotated[
    list[ClickProviderConfig], BeforeValidator(FieldValidator.coerce(list, transform=_wrap_in_list))
]
_DictProviders = Annotated[
    list[DictProviderConfig], BeforeValidator(FieldValidator.coerce(list, transform=_wrap_in_list))
]
_EnvVarProviders = Annotated[
    list[EnvVarProviderConfig], BeforeValidator(FieldValidator.coerce(list, transform=_wrap_in_list))
]
_JsonFileProviders = Annotated[
    list[JsonProviderConfig], BeforeValidator(FieldValidator.coerce(list, transform=_wrap_in_list))
]


class ProviderConfigModel(BaseModel):
    """
    Model for configuring configuration providers.
    """

    argparse_provider: _ArgparseProviders = Field(
        description="Configuration for the argparse provider.",
        default_factory=list,
    )

    click_provider: _ClickProviders = Field(
        description="Configuration for the Click provider.",
        default_factory=list,
    )

    dict_provider: _DictProviders = Field(
        description="Configuration for the dict provider.",
        default_factory=list,
    )

    env_var_provider: _EnvVarProviders = Field(
        description="Configuration for the environment variable provider.",
        default_factory=list,
    )

    json_file_provider: _JsonFileProviders = Field(
        description="Configuration for the JSON file provider.",
        default_factory=list,
    )

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            argparse_provider: ArgparseProviderConfig | list[ArgparseProviderConfig] = ...,
            click_provider: ClickProviderConfig | list[ClickProviderConfig] = ...,
            dict_provider: DictProviderConfig | list[DictProviderConfig] = ...,
            env_var_provider: EnvVarProviderConfig | list[EnvVarProviderConfig] = ...,
            json_file_provider: JsonProviderConfig | list[JsonProviderConfig] = ...,
        ) -> None: ...
