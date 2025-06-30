
from flask import Flask, request, jsonify
import hmac
import hashlib
import time
import threading

import requests

API_KEY = "mx0vgIVayWC5Luvjup"
API_SECRET = "6d0f19510b814546aecd3ef47d287f65"
BASE_URL = "https://contract.mexc.com"

app = Flask(__name__)

def sign(params, secret):
    sorted_params = sorted(params.items())
    query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    signature = hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return signature

def place_order(pair, side, leverage, capital_percent):
    print(f"Received signal: {side.upper()} {pair} at {leverage}x using {capital_percent}% capital")

    # Placeholder for account balance (replace with real API call if needed)
    balance = 10000
    order_amount = balance * (capital_percent / 100)

    # Simulated request to MEXC (you will replace this with real order code)
    print(f"Placing {side.upper()} order on {pair} with ${order_amount:.2f} at {leverage}x leverage.")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Webhook received:", data)

    required_keys = ["pair", "side", "leverage", "capital_percent"]
    if not all(k in data for k in required_keys):
        return jsonify({"error": "Missing required data"}), 400

    # Run trading logic in background
    threading.Thread(target=place_order, args=(
        data["pair"],
        data["side"],
        data["leverage"],
        data["capital_percent"]
    )).start()

    return jsonify({"status": "order received"}), 200

if __name__ == "__main__":
    print("🚀 Webhook sniper bot is running on http://localhost:5000/webhook")
    app.run(host="0.0.0.0", port=5000)
