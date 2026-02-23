# email_intake_poc/tools/validation_tools.py

from email_intake_poc.sub_agents.validation_agent.agent import ValidationAgent

_validation_agent = ValidationAgent()

def validate_rma(selected_email: dict):
    """
    Validate a single extracted RMA object.
    Returns None if valid, or an error JSON if invalid.
    """
    return _validation_agent.validate(selected_email)