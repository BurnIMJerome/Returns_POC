import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rma_tool")

def submit_rma(customer_id):
    """
    Submit an RMA by making a POST request to the Power Automate API.

    Args:
        customer_id (str): The Customer_ID to include in the payload.

    Returns:
        dict: The API response and status code.
    """
    url = "https://320da500b1c942b5821790fc274f46.a4.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/2dc274d1b3834530a1ef5750fd35339b/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=5WqomQ1HEcScO7CWlm3P_oYzHysocd-xzsjrU87pAsM"

    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "Customer_ID": customer_id
    }

    try:
        logger.info("Sending POST request to API.")
        logger.info(f"URL: {url}")
        logger.info(f"Payload: {payload}")
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        return {"status_code": response.status_code, "response": response.json()}
    except requests.exceptions.RequestException as e:
        logger.error("Error occurred during API call.")
        logger.error(f"Error details: {e}")
        return {"error": str(e)}