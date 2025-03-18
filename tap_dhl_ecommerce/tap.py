"""DHL Ecommerce tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th

from tap_dhl_ecommerce import streams


class Tapdhlecommerce(Tap):
    """DHL Ecommerce tap class."""

    name = "tap-dhl-ecommerce"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "pickup_id",
            th.StringType,
            required=True,
            secret=False,
            title="Pickup ID",
            description="The ID for the pickup account to use.",
        ),
        th.Property(
            "client_id",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            title="Client ID",
            description="The client ID for use in retrieving an access token.",
        ),
        th.Property(
            "client_secret",
            th.StringType,
            required=True,
            secret=True,  # Flag config as protected.
            title="Client Secret",
            description="The client secret for use in retrieving an access token.",
        ),
    ).to_dict()

    def discover_streams(self) -> list[streams.dhlecommerceStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.PackagesStream(self),
        ]


if __name__ == "__main__":
    Tapdhlecommerce.cli()
