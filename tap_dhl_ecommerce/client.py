"""REST client handling, including DhlEcommerceStream base class."""

from __future__ import annotations

import typing as t
from importlib import resources
import requests
import base64

from singer_sdk.authenticators import BearerTokenAuthenticator
from singer_sdk.streams import RESTStream

if t.TYPE_CHECKING:
    import requests
    from singer_sdk.helpers.types import Context


SCHEMAS_DIR = resources.files(__package__) / "schemas"


class DhlEcommerceStream(RESTStream):
    """dhlecommerce stream class."""

    records_jsonpath = "$.results[*]"

    next_page_token_jsonpath = "$.next_page"  # noqa: S105

    @property
    def url_base(self) -> str:
        """Return the API URL root."""
        return "https://api.dhlecs.com/"
    
    @property
    def authenticator(self) -> BearerTokenAuthenticator:
        """Requests an access token from the DHL eCommerce Americas API.

        Returns:
            An access token.
        """
        url = "https://api.dhlecs.com/auth/v4/accesstoken"
        payload="grant_type=client_credentials"
        client_id = self.config.get("client_id")
        client_secret = self.config.get("client_secret")

        encoded_credentials = base64.b64encode(
            f"{client_id}:{client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        access_token = response.json()["access_token"]
        if not access_token:
            raise ValueError("Failed to obtain access token.")

        return access_token
