import requests
import os
from dotenv import load_dotenv

# Load env variables from .env file (local development)
load_dotenv()

def get_exchange_rate(base_currency, target_currency):
    API_KEY = os.getenv("FIXER_API_KEY")
    url = f"http://data.fixer.io/api/latest?access_key={API_KEY}"

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
