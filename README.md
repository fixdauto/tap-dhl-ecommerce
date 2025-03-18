# tap-dhlecommerce

`tap-dhl-ecommerce` is a Singer tap for DHL eCommerce Americas.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Features
- Leverages the `tracking` endpoint from the [DHL eCommerce Americas API](https://docs.api.dhlecs.com/)
in order to grab package tracking status updates.
- Built with the Singer SDK for extensibility and Meltano compatibility.

## Requirements

- Python 3.9+

- DHL eCommerce Americas Client ID & Secret

- Singer SDK

- Meltano (optional, for pipeline orchestration)

## Installation

1. Clone the repository:
  ```bash
  git clone https://github.com/fixdauto/tap-dhl-ecommerce.git
  cd tap-dhl-ecommerce
  ```
2. Install the dependencies:
  ```bash
  poetry install
  ```
3. Activate the Poetry virtual environment:
  ```bash
  poetry shell
  ```

## Configuration

1. Create a config.json file with the following structure:
  ```bash
  {
    "pickup_id": "YOUR_DHL_ACCOUNT_PICKUP_ID",
    "client_id": "YOUR_DHL_CLIENT_ID",
    "client_secret": "YOUR_DHL_CLIENT_SECRET"
  }
  ```
  - `pickup_id`: Your DHL eCommerce Americas account pickup ID.

  - `client_id`: Your DHL eCommerce Americas client ID.

  - `client_secret`: Your DHL eCommerce Americas client secret.

2. Place config.json in the root directory or pass its path as an argument when running the tap.

## Running the Tap

1. Run the tap standalone:
  ```bash
  poetry run python -m tap_dhl_ecommerce --config config.json
  ```
2. Use with Meltano for pipeline orchestration:
  - Add the tap to your Meltano project:
  ```bash
  meltano add extractor tap-dhl-ecommerce
  ```
  - Configure the tap in meltano.yml:
  ```bash
  extractors:
    tap-dhl-ecommerce:
      config:
        pickup_id: YOUR_DHL_ACCOUNT_PICKUP_ID
        client_id: YOUR_DHL_CLIENT_ID
        client_secret: YOUR_DHL_CLIENT_SECRET
  ```
  - Run the tap via Meltano:
  ```bash
  meltano run tap-dhl-ecommerce target-your-target
  ```

### Accepted Config Options

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-dhl-ecommerce --about
```

### Configure using environment variables

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

### Testing with [Meltano](https://www.meltano.com)

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-dhl-ecommerce
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-dhl-ecommerce --version
# OR run a test `elt` pipeline:
meltano run tap-dhl-ecommerce target-jsonl
```

## Customization

The streams.py file provides the main logic for fetching and processing data. Key points
of customization include:
- **Date Range:** Modify the date range being requested by changing the `start_date` variable in the `get_records` method.

- **Date Interval:** This script defaults to requesting data day by day, but that can be adjusted by changing the `interval_in_days` parameter in the `date_range` method.

## Development

1. Install development dependencies using Poetry:
  ```bash
  poetry install --with dev
  ```
2. Run tests:
  ```bash
  poery run pytest
  ```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the SDK to
develop your own taps and targets.
