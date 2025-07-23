import xmlrpc.client
import requests
import json
from datetime import datetime

# === Odoo Credentials ===
url = "https://excel-engineering-private-limited.odoo.com"
db = "excel-engineering-private-limited"
username = "altafhussainslara@gmail.com"
password = "@Altaf12"  # Use API key if applicable

# === FBR Credentials ===
fbr_url = "https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb"
bearer_token = "3124e65b-0501-3e90-9c53-ceea5aabad00"

# === Connect to Odoo ===
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# === Fetch posted customer invoices ===
invoice_ids = models.execute_kw(
    db, uid, password,
    'account.move', 'search',
    [[['move_type', '=', 'out_invoice'], ['state', '=', 'posted']]],
    {'limit': 1}
)

invoices = models.execute_kw(
    db, uid, password,
    'account.move', 'read',
    [invoice_ids],
    {'fields': ['name', 'invoice_date', 'partner_id', 'invoice_line_ids', 'amount_total']}
)

# === Prepare payload ===
fbr_payload = {
    "invoiceType": "Sale Invoice",
    "invoiceDate": invoices[0]['invoice_date'],
    "sellerNTNCNIC": "1234567890123",
    "sellerBusinessName": "Excel Engineering Private Limited",
    "sellerProvince": "Punjab",
    "sellerAddress": "Lahore, Pakistan",
    "buyerNTNCNIC": "0000000000000",
    "buyerBusinessName": invoices[0]['partner_id'][1],
    "buyerProvince": "Punjab",
    "buyerAddress": "Unknown",
    "buyerRegistrationType": "Registered",
    "invoiceRefNo": invoices[0]['name'],
    "scenarioId": "SN000",
    "items": []
}

# === Fetch invoice line details ===
line_ids = invoices[0]['invoice_line_ids']
lines = models.execute_kw(
    db, uid, password,
    'account.move.line', 'read',
    [line_ids],
    {'fields': ['name', 'quantity', 'price_unit', 'price_subtotal']}
)

# === Map lines to FBR items ===
for line in lines:
    item = {
        "hsCode": "0000.0000",  # You can enhance this by reading from product
        "productDescription": line['name'],
        "rate": "18%",
        "uoM": "Nos",
        "quantity": line['quantity'],
        "totalValues": line['price_subtotal'],
        "valueSalesExcludingST": line['price_subtotal'],
        "fixedNotifiedValueOrRetailPrice": 0,
        "salesTaxApplicable": 0,
        "salesTaxWithheldAtSource": 0,
        "extraTax": "",
        "furtherTax": 0,
        "sroScheduleNo": "",
        "fedPayable": 0,
        "discount": 0,
        "saleType": "TaxInvoice",
        "sroItemSerialNo": ""
    }
    fbr_payload["items"].append(item)

# === Send to FBR ===
headers = {
    "Authorization": "Bearer Token:3124e65b-0501-3e90-9c53-ceea5aabad00",  # ⚠️ NOT Token:
    "Content-Type": "application/json"
}
print("payload",json.dumps(fbr_payload,indent=2))
print("Using token:", headers["Authorization"])
response = requests.post(fbr_url, headers=headers, data=json.dumps(fbr_payload), verify=False)

# === Output Response ===
print("FBR Response Status Code:", response.status_code)
print("FBR Response:", response.text)
