from typing import Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelValidator:
    """
    Utility class for validating partial dictionaries against Pydantic models.
    This is useful for validating subsets of configuration data against their corresponding models, such as when
    validating kwargs or environment variables.
    """

    @staticmethod
    def _generate_partial_model(model: type[T]) -> type[T]:
        fields = {name: (Optional[info.annotation], None) for name, info in model.model_fields.items()}
        partial_model = type(
            f"Partial{model.__name__}",
            (BaseModel,),
            {"__annotations__": {k: v[0] for k, v in fields.items()}, **{k: v[1] for k, v in fields.items()}},
        )

        return partial_model

    @staticmethod
    def validate_partial_model(model: type[T], data: dict):
        """
        Validate a partial dictionary against a Pydantic model.
        This method checks if the provided data can be used to create a valid instance of the model,
        even if not all required fields are present. It returns True if the data is valid, and False otherwise.
        """

        partial_model = ModelValidator._generate_partial_model(model)
        partial_model.model_validate(data)
