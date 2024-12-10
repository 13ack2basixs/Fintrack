import requests
import os
from dotenv import load_dotenv

# Load env variables from .env file (local development)
load_dotenv()

def get_exchange_rate(base_currency, target_currency):
    FIXER_API_KEY = os.getenv("FIXER_API_KEY")
    url = f"http://data.fixer.io/api/latest?access_key={FIXER_API_KEY}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            rates = data["rates"]
            base_rate = rates.get(base_currency)
            target_rate = rates.get(target_currency)
            # Formula: SGD -> MYR = MYR -> EUR / SGD -> EUR

            if base_rate and target_rate:
                # Indirect conversion using EUR as intermediary
                return target_rate / base_rate
            else:
                raise ValueError(f"Invalid currency: {base_currency} or {target_currency}")
        else:
            raise Exception(f"Fixer.io API Error: {data.get('error', {}).get('info', 'Unknown error')}")
    else:
        raise Exception(f"HTTP Error: {response.status_code}")

def convert_to_sgd(amount, currency):
    if currency == 'SGD':
        return amount
    try:
        exchange_rate = get_exchange_rate(currency, "SGD")
        return float(amount) * exchange_rate
    except Exception as e:
        raise ValueError(f"Currency conversion error: {str(e)}")
    
# App sends request to PayPal's OAuth2 endpoint, returns access token if valid
# Access token required to proceed (Authentication)
def get_access_token():
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"

    # Translate from cURL command to Python equivalent
    # Sends POST request and gets back JSON response
    response = requests.post(
        url, 
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        error_message = response.json().get('error_description', 'Unknown error')
        raise Exception(f"PayPal API Error: {error_message}")
    
def create_paypal_payment(amount, return_url, cancel_url):

    # Request Sample from PayPal docs
    access_token = get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    data = { 
        "intent": "CAPTURE", 
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "SGD",
                    "value": f"{amount:.2f}"
                },
            }
        ],
        "payment_source": { 
            "paypal": { 
                "experience_context": {
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                },
            } 
        } 
    } 

    # Sends POST request and get back JSON response
    response = requests.post(
        'https://api-m.sandbox.paypal.com/v2/checkout/orders', 
        headers=headers, 
        json=data
    )
    if response.status_code == 200:
        payment_data = response.json()
        payer_action = next(
            link["href"]
            for link in payment_data["links"]
            if link["rel"] == "payer-action"
        )
        return payer_action # URL link to PayPal Payment Page
    else:
        error_message = response.json().get('details', [{'issue': 'Unknown error'}])[0].get('issue', 'Unknown error')
        raise Exception(f"PayPal API Error: {error_message}")
