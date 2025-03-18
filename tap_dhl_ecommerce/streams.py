"""Stream type classes for tap-dhl-ecommerce."""

from __future__ import annotations

import typing as t
from importlib import resources
import requests
import pandas as pd
import pytz

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from singer_sdk import typing as th, metrics

if t.TYPE_CHECKING:
    import requests
    from singer_sdk.helpers.types import Context

from tap_dhl_ecommerce.client import DhlEcommerceStream

SCHEMAS_DIR = resources.files(__package__) / "schemas"

class PackagesStream(DhlEcommerceStream):
    """Uses the Reporting API to get aggregated ad & campaign data in JSON format."""

    name = "packages"
    path = "tracking/v4/package/open"
    primary_keys: t.ClassVar[list[str]] = ["dhl_package_id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "packages.json"  # noqa: ERA001
    records_jsonpath = "$.packages[*]"


    @staticmethod
    def date_range(
        start_date: datetime, end_date: datetime, interval_in_days: int = 1
    ) -> t.Iterator[t.Tuple[datetime, datetime]]:
        """
        Generator that yields tuples representing date intervals between start_date and end_date.

        Args:
            start_date (datetime): Start of the period.
            end_date (datetime): End of the period.
            interval_in_days (int): Number of days per interval.

        Yields:
            Tuple[datetime, datetime]: Start and end of each interval.
        """
        current_date = start_date
        while current_date < end_date:
            interval_start = current_date
            interval_end = current_date + timedelta(days=interval_in_days)

            if interval_end > end_date:
                interval_end = end_date

            yield interval_start, interval_end
            current_date = interval_end


    def get_url_params(
        self, context: t.Optional[Context], next_page_token: t.Any = None
    ) -> dict[str, t.Any]:
        """
        Return URL parameters for the request.

        Args:
            context: The stream context.
            next_page_token: The next page token.

        Returns:
            dict: URL query parameters.
        """
        return {"pickup": self.config.get("pickup_id")}


    def _convert_to_eastern(self, date_str: str, time_str: str, timezone_str: str) -> t.Optional[datetime]:
        """
        Convert date and time strings to a timezone-aware datetime in Eastern Time.

        Args:
            date_str (str): Date in YYYY-MM-DD format.
            time_str (str): Time in HH:MM:SS format.
            timezone_str (str): Timezone indicator (e.g. "ET" or another).

        Returns:
            Optional[datetime]: The converted datetime in Eastern Time, or None if parsing fails.
        """
        try:
            naive_dt = pd.to_datetime(f"{date_str} {time_str}", format="%Y-%m-%d %H:%M:%S")
        except Exception as e:
            self.logger.error(f"Failed to parse date/time: {e}")
            return None
        eastern = pytz.timezone("America/New_York")
        if timezone_str == "ET":
            return eastern.localize(naive_dt)
        else:
            original_tz = pytz.timezone("UTC")
            dt_orig = original_tz.localize(naive_dt)
            return dt_orig.astimezone(eastern)


    def parse_record(self, record: t.Any) -> dict:
        """
        Parse a single record from the API response.

        Args:
            record: The raw record dictionary.

        Returns:
            dict: The parsed record.
        """
        parsed: dict[str, t.Any] = {
            "events": record.get("events", []),
            "recipient_city": record.get("recipient", {}).get("city"),
            "recipient_country": record.get("recipient", {}).get("country"),
            "recipient_postal_code": record.get("recipient", {}).get("postalCode"),
            "recipient_state": record.get("recipient", {}).get("state"),
            "package_weight_lbs": record.get("package", {}).get("weight", {}).get("value"),
            "package_product_name": record.get("package", {}).get("productName"),
            "package_product_class": record.get("package", {}).get("productClass"),
            "dhl_package_id": record.get("package", {}).get("dhlPackageId"),
            "customer_package_id": record.get("package", {}).get("packageId"),
            "is_delivered": False,
        }

        for event in record.get("events", []):
            if event.get("primaryEventDescription") == "LABEL CREATED":
                eastern_dt = self._convert_to_eastern(
                    event.get("date"), event.get("time"), event.get("timeZone")
                )
                if eastern_dt:
                    parsed["label_created_at"] = eastern_dt
            elif event.get("primaryEventDescription") == "DELIVERED":
                eastern_dt = self._convert_to_eastern(
                    event.get("date"), event.get("time"), event.get("timeZone")
                )
                if eastern_dt:
                    parsed["delivered_at"] = eastern_dt
                parsed["is_delivered"] = True

        return parsed


    def get_records(self, context: t.Optional[dict[str, t.Any]]) -> t.Iterator[dict]:
        """
        Generator yielding parsed records for the stream.

        Args:
            context (Optional[dict]): Stream context.

        Yields:
            dict: Parsed record.
        """
        self.logger.info(f"tap_states: {self.tap_state}")

        url: str = self.get_url(context)
        base_params: dict[str, t.Any] = self.get_url_params(context, next_page_token=None)
        headers = {"Authorization": f"Bearer {self.authenticator}"}
        
        with requests.Session() as session:
            start_date = datetime.now() - relativedelta(days=20)
            end_date = datetime.now()
            state_dict = self.get_context_state(context)

            self.logger.info(f"state_dict: {state_dict}")
            self.logger.info(f"tap_states: {self.tap_state}")

            for interval_start, interval_end in self.date_range(start_date, end_date):
                interval_start = interval_start.strftime("%Y-%m-%d")
                interval_end = interval_end.strftime("%Y-%m-%d")
                if interval_start == interval_end:
                    break
                self.logger.info(f"requesting data from {interval_start} to {interval_end}")
                offset = 0
                params = base_params.copy()
                params["startDate"] = interval_start
                params["endDate"] = interval_end
                while True:
                    try:
                        params["offset"] = offset
                        response = session.get( url=url, headers=headers, params=params)
                        response.raise_for_status()
                        response_json = response.json()
                        records = response_json.get("packages", [])
                        total_records = response_json.get("total", 0)
                        if total_records == 0 or not records:
                            self.logger.info(
                                f"{self.name}: No more records to fetch from {interval_start} - {interval_end}"
                            )
                            break
                        
                        self.logger.info(
                            f"{self.name}: Fetched {len(records)} records from {interval_start} - {interval_end}"
                        )

                        for record in records:
                            yield self.parse_record(record)

                        self.logger.info(
                            f"{self.name}: Processed offset {offset} of {total_records} records at {datetime.utcnow()}"
                            )
                        offset += 10
                    except requests.exceptions.RequestException as e:
                        self.logger.error(f"{self.name}: Failed to process records from {interval_start} - {interval_end}")
                        self.logger.error(f"Exception: {str(e)}")
                        break
