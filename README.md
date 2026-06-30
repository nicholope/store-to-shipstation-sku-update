# ShipStation SKU Updater

Fetches all `awaiting_shipment` orders from a ShipStation store, remaps store-facing SKUs to supplier SKUs using a CSV lookup table, and updates the orders in ShipStation via the API.

## How it works

1. Fetches all awaiting shipment orders for the configured store
2. Filters out items whose SKU already starts with `2` (already a supplier SKU)
3. Looks up the supplier SKU from `sku_mapping.csv`
4. Fetches the full order JSON, updates the SKU field, and POSTs it back to ShipStation

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/nicholope/store-to-shipstation-sku-update.git
cd store-to-shipstation-sku-update
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install python-dotenv requests
```

### 3. Configure environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `SHIPSTATION_API_KEY` | Your ShipStation API key |
| `SHIPSTATION_API_SECRET` | Your ShipStation API secret |
| `SHIPSTATION_STORE_ID` | The numeric ID of your ShipStation store |
| `SUPPLIER_SKU_PREFIX` | The character(s) that supplier SKUs start with — used to skip orders already updated (e.g. `2`) |

Your API key and secret can be found in ShipStation under **Account Settings → API Settings**.

### 4. Update the SKU mapping

`sku_mapping.csv` contains two columns:

| Column | Description |
|---|---|
| `store_sku` | The marketplace SKU (e.g. `40412960-000-002`) |
| `supplier_sku` | The supplier SKU to replace it with (e.g. `21403S-101A135`) |

Edit this file directly or export a new version from your product catalog spreadsheet. See `sku_mapping.example.csv` for the expected format.

### 5. Run

```bash
python sku_update.py
```

## Running on GitHub Actions

Store your credentials as repository secrets in **Settings → Secrets and variables → Actions**:

- `SHIPSTATION_API_KEY`
- `SHIPSTATION_API_SECRET`
- `SHIPSTATION_STORE_ID`
- `SUPPLIER_SKU_PREFIX`

Create the file `.github/workflows/sku_update.yml`:

```yaml
name: Update ShipStation SKUs

on:
  workflow_dispatch:  # run manually from the Actions tab
  schedule:
    - cron: '0 9 * * 1-5'  # weekdays at 9am UTC — adjust to your timezone

jobs:
  update-skus:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install python-dotenv requests

      - name: Run SKU update
        env:
          SHIPSTATION_API_KEY: ${{ secrets.SHIPSTATION_API_KEY }}
          SHIPSTATION_API_SECRET: ${{ secrets.SHIPSTATION_API_SECRET }}
          SHIPSTATION_STORE_ID: ${{ secrets.SHIPSTATION_STORE_ID }}
          SUPPLIER_SKU_PREFIX: ${{ secrets.SUPPLIER_SKU_PREFIX }}
        run: python sku_update.py
```

The `workflow_dispatch` trigger lets you run it manually from the Actions tab at any time. The `schedule` trigger runs it automatically — adjust the cron expression to match when you want it to run. A handy reference: [crontab.guru](https://crontab.guru).

> **Note:** The script makes live changes to ShipStation orders when run. Test with a non-production store first if possible.
