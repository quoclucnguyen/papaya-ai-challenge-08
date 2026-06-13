"""Base validator and default validator registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from src.models.base import ExtractionResult, ValidationError


class BaseValidator(ABC):
    """Base class for all validators."""

    @abstractmethod
    def validate(self, result: ExtractionResult) -> list[ValidationError]:
        """Validate an extraction result."""


class ValidatorRegistry:
    """Registry that runs a configured set of validators."""

    def __init__(self, validators: Iterable[BaseValidator] = ()) -> None:
        self._validators = list(validators)

    def register(self, validator: BaseValidator) -> None:
        """Register a validator."""
        self._validators.append(validator)

    def validate(self, result: ExtractionResult) -> list[ValidationError]:
        """Run all validators on a result."""
        errors: list[ValidationError] = []
        for validator in self._validators:
            errors.extend(validator.validate(result))
        return errors


_registry: ValidatorRegistry | None = None


def register_validator(validator: BaseValidator) -> None:
    """Register an additional validator globally."""
    get_registry().register(validator)


def validate_result(result: ExtractionResult) -> list[ValidationError]:
    """Validate a result using all default validators."""
    return get_registry().validate(result)


def get_registry() -> ValidatorRegistry:
    """Build the default registry lazily to avoid import side effects."""
    global _registry
    if _registry is None:
        from src.validators.amounts import AmountValidator
        from src.validators.confidence import ConfidenceValidator
        from src.validators.dates import DateValidator
        from src.validators.sums import SumValidator

        _registry = ValidatorRegistry(
            [
                DateValidator(),
                AmountValidator(),
                SumValidator(),
                ConfidenceValidator(),
            ]
        )
    return _registry
