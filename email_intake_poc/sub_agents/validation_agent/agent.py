__all__ = ["ValidationAgent", "validation_agent"]
class ValidationAgent:
    REQUIRED_FIELDS = ["RMA_ID", "Customer_ID"]
    EITHER_FIELDS = ["Order_Number", "Invoice_Number"]

validation_agent = ValidationAgent()

def validate(self, row):
        """
        Validate exactly ONE RMA row.
        Returns:
          - None if valid
          - dict with business-readable error if invalid
        """

        missing_fields = []

        # Required fields
        for field in self.REQUIRED_FIELDS:
            if not row.get(field):
                missing_fields.append(field)

        # Either Order_Number or Invoice_Number
        has_order_or_invoice = any(row.get(field) for field in self.EITHER_FIELDS)
        if not has_order_or_invoice:
            missing_fields.extend(self.EITHER_FIELDS)

        if missing_fields:
            return {
                "status": "error",
                "error_type": "validation_error",
                "message": (
                    "We’re missing some required information to create the RMA. "
                    "Please review the details below and resend the request."
                ),
                "missing_information": sorted(set(missing_fields)),
                "business_guidance": (
                    "An RMA request must include a Customer ID and at least one "
                    "reference number (either an Order Number or an Invoice Number)."
                ),
                "next_step": (
                    "Please provide the missing information and submit the RMA request again."
                ),
            }

        # Valid RMA
        return None