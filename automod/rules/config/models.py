from dataclasses import dataclass

from ..base import BaseRule


@dataclass
class EmbedField:
    name: str
    value: str


@dataclass
class InfractionInformation:
    message: str
    rule: BaseRule = None
    extra_fields: [EmbedField] = None
    # i guess i can add more here for other rules - maybe?
