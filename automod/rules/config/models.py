from dataclasses import dataclass
from enum import Enum

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
    embed_description: str = None
    # i guess i can add more here for other rules - maybe?


class BlackOrWhiteList(Enum):
    Blacklist = (1,)
    Whitelist = 2
