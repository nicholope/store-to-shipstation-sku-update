# -*- coding: utf-8 -*-
import base64
import csv
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["SHIPSTATION_API_KEY"]
api_secret = os.environ["SHIPSTATION_API_SECRET"]

combined_string = f"{api_key}:{api_secret}"
encoded_string = base64.b64encode(combined_string.encode()).decode()
authorization_header = f"Basic {encoded_string}"

storeId = os.environ["SHIPSTATION_STORE_ID"]
supplier_sku_prefix = os.environ["SUPPLIER_SKU_PREFIX"]
orderStatus = 'awaiting_shipment'

with open("sku_mapping.csv", newline="") as f:
    supplier_sku_lookup = {row["store_sku"]: row["supplier_sku"] for row in csv.DictReader(f)}

search_url = "https://ssapi.shipstation.com/orders"
headers = {'Authorization': authorization_header}
params = {'storeId': storeId, 'orderStatus': orderStatus}

response = requests.get(search_url, headers=headers, params=params)

order_details = []
if response.status_code == 200:
    for order in response.json().get('orders', []):
        po_number = order.get('orderNumber')
        order_id = order.get('orderId')
        order_key = order.get('orderKey')
        for item in order.get('items', []):
            order_details.append({
                'poNumber': po_number,
                'orderId': order_id,
                'orderKey': order_key,
                'sku': item.get('sku'),
            })
else:
    print(f"Query failed with status code {response.status_code}: {response.text}")

# Filter items that haven't been mapped yet (store SKUs don't start with '2')
order_details_clean = []
for detail in order_details:
    sku = detail['sku']
    if not sku.startswith(supplier_sku_prefix):
        order_details_clean.append({
            'poNumber': detail['poNumber'],
            'orderId': detail['orderId'],
            'orderKey': detail['orderKey'],
            'sku': sku,
            'sku2': supplier_sku_lookup.get(sku, sku),
        })

print(order_details_clean)

# Fetch full order JSON, update SKU, collect for POST
updated_responses = []
for detail in order_details_clean:
    order_url = f"https://ssapi.shipstation.com/orders/{detail['orderId']}"
    order_response = requests.get(order_url, headers={'Host': 'ssapi.shipstation.com', 'Authorization': authorization_header})
    json_data = order_response.json()

    for item in json_data.get('items', []):
        if 'sku' in item:
            item['sku'] = detail['sku2']

    updated_responses.append(json.dumps(json_data, indent=4))

for r in updated_responses:
    print(r)

# POST updated orders back to ShipStation
create_url = "https://ssapi.shipstation.com/orders/createorder"
create_headers = {
    'Host': 'ssapi.shipstation.com',
    'Authorization': authorization_header,
    'Content-Type': 'application/json',
}

for payload in updated_responses:
    post_response = requests.post(create_url, headers=create_headers, data=payload)
    print(post_response.text.encode('utf8'))
