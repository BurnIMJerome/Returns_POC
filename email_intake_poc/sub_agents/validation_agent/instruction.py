# Validation rules for each field
VALIDATION_RULES = {
    "RMA_ID": {"required": True, "numeric": True},
    "Customer_ID": {"required": True, "numeric": True},
    "Order_Number": {"required": True},
    "Invoice_Number": {"required": True},
}
