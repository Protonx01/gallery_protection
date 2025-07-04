
from frappe.handler import handle
from frappe import _

def cors_handler():
    from frappe import local
    response = handle()
    if local.response:
        local.response.headers["Access-Control-Allow-Origin"] = "*"
        local.response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        local.response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response