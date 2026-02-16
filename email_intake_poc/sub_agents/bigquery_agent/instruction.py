bigquery_agent_instruction = """
Parse {{email_records}} stored from email_agent:

Count how many email items exist, then respond EXACTLY:

<N> emails inserted successfully to bigquery

Inserted Emails:
- ID: <id>
  Subject: <subject>
"""