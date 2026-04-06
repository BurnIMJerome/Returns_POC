from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from email_intake_poc.sub_agents.email_agent.agent import email_agent
from email_intake_poc.sub_agents.bigquery_insert_agent.agent import bigquery_insert_agent
from email_intake_poc.sub_agents.bigquery_retrieval_agent.agent import bigquery_retrieval_agent
from email_intake_poc.tools.rma_tool import submit_rma

from .instruction import main_agent_instruction
from .config import settings
from google.adk.models import LlmResponse
import copy 
from typing import Dict, Optional, Literal, Union, Any
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
# Guardrails import
from .guardrails import (
    before_model_guard,
)

def after_model_callback_def(callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    After the model produces output, this callback just save the response in state.
    """
       # Validate structure safely
    if (
        not llm_response
        or not llm_response.content
        or not llm_response.content.parts
        or len(llm_response.content.parts) == 0
        or not hasattr(llm_response.content.parts[0], "text")
        or not llm_response.content.parts[0].text
        or not llm_response.content.parts[0].text.strip()
    ):
         print("\n[AFTER MODEL] LLM response is empty or malformed. No modifications.")
         return llm_response
    
    modified_llm_response = copy.deepcopy(llm_response)

    # Assuming the main text is in the first part
    original_text = modified_llm_response.content.parts[0].text
    current_text = original_text  # Start with original for modification

    print(f"\n[AFTER MODEL] Original LLM response: '{original_text}'")
    callback_context.state["main_agent_response"] = original_text
    
    return None

root_agent = LlmAgent(
    name="email_intake_poc",
    model=settings.GOOGLE_MODEL,tools=[submit_rma] ,
    instruction=main_agent_instruction,
    sub_agents=[email_agent, bigquery_retrieval_agent],
    before_model_callback=before_model_guard,# Gaurdrails call
    #after_model_callback=after_model_callback_def
    #tools=[read_unread_inbox, read_latest_inbox, read_message_full],
)