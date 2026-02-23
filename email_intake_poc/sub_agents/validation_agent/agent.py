class ValidationAgent:
    # Fields required for validation
    REQUIRED_FIELDS = ["Customer_ID"]
    EITHER_FIELDS = ["Order_Number", "Invoice_Number"]

    # Public method to validate a single RMA object
    def validate(self, row: dict):
        """
        Validate a single extracted RMA object.
        Returns None if valid, or a JSON error dict if invalid.
        """
        missing_fields = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if not row.get(field):
                missing_fields.append(field)

        # Check at least one of Order_Number or Invoice_Number exists
        if not any(row.get(f) for f in self.EITHER_FIELDS):
            missing_fields.extend(self.EITHER_FIELDS)

        # Return error JSON if validation fails
        if missing_fields:
            return {
                "status": "error",
                "error_type": "validation_error",
                "message": "Required RMA identifiers are missing.",
                "missing_fields": sorted(set(missing_fields)),
                "next_step": (
                    "Ensure Customer_ID and either Invoice_Number or "
                    "Order_Number are present before retrying."
                ),
            }

        # If all required fields exist, validation passes
        return None