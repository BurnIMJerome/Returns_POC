from .instruction import VALIDATION_RULES

class ValidationAgent:
    def __init__(self, bigquery_agent):
        self.bigquery_agent = bigquery_agent

    def validate_row(self, row):
        errors = []

        for field, rules in VALIDATION_RULES.items():
            value = row.get(field, "")
            if rules.get("required") and not value:
                errors.append(f"{field} is empty.")
            if rules.get("numeric") and value and not value.isdigit():
                errors.append(f"{field} must be numeric.")

        # Optional: check RMA_ID in BigQuery
        rma_id = row.get("RMA_ID")
        if rma_id and self.bigquery_agent:
            query = f"SELECT COUNT(*) FROM Orders WHERE RMA_ID='{rma_id}'"
            exists = self.bigquery_agent.query(query)
            if not exists or (len(exists) > 0 and exists[0].get("f0_") == 0):
                errors.append(f"RMA_ID '{rma_id}' not found in BigQuery.")

        return errors

    def process_rows(self, rows):
        all_errors = {}
        for row in rows:
            row_errors = self.validate_row(row)
            if row_errors:
                all_errors[row.get("RMA_ID", "Unknown")] = row_errors

        if not all_errors:
            return "✅ All rows passed validation."
        reply_lines = ["⚠️ Validation Errors Found:"]
        for rma_id, errs in all_errors.items():
            reply_lines.append(f"RMA_ID: {rma_id}")
            reply_lines.extend([f"  - {e}" for e in errs])
        return "\n".join(reply_lines)
