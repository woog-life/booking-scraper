import os
from dataclasses import dataclass
from uuid import UUID


@dataclass
class Configuration:
    lake_id: UUID
    variation: str
    query: str
    api_key: str


def _determine_configuration() -> Configuration:
    config = os.getenv("LAKE_NAME")
    api_key = os.getenv("API_KEY")
    if config == "woog-family":
        return Configuration(
            lake_id=UUID(os.getenv("LARGE_WOOG_UUID")),
            variation="Badestelle Familienbad",
            query="Landgraf-Georg-Straße 121 * 64287 Darmstadt",
            api_key=api_key,
        )
    elif config == "woog-island":
        return Configuration(
            lake_id=UUID(os.getenv("LARGE_WOOG_UUID")),
            variation="Woog Badestelle Insel",
            query="Heinrich-Fuhr-Str. 20 * 64287 Darmstadt",
            api_key=api_key,
        )
    elif config == "muehlchen":
        return Configuration(
            lake_id=UUID(os.getenv("ARHEILGER_MUEHLCHEN_UUID")),
            variation="Naturbadesee Arheilger Mühlchen",
            query="Brücherweg 1 * 64291 Darmstadt",
            api_key=api_key,
        )
    else:
        raise ValueError("Invalid or unset 'LAKE_NAME'")


configuration = _determine_configuration()
