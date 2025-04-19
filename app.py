import os
import json
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Helper: scrape price and title from Flipkart
def scrape_price_and_title(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Get product title (class updated for Flipkart)
        title_tag = soup.find("span", {"class": "VU-ZEz"}) or soup.find("span", {"class": "B_NuCI"})
        product_name = title_tag.text.strip() if title_tag else "Product title not found"

        # Get product price using the updated class
        price_tag = soup.find("div", {"class": "Nx9bqj CxhGGd"})  # Correct class for price
        price_text = price_tag.text.strip().replace("₹", "").replace(",", "") if price_tag else "0"
        current_price = int(price_text) if price_text.isdigit() else 0

        return product_name, current_price
    except Exception:
        return "Product title not found", 0

# Helper: check if scraping should occur based on frequency
def should_scrape(last_checked_str, frequency):
    try:
        last_checked = datetime.fromisoformat(last_checked_str)
        now = datetime.now()
        diff = (now - last_checked).total_seconds()

        if frequency == "hourly":
            return diff >= 3600
        elif frequency == "daily":
            return diff >= 86400
        elif frequency == "weekly":
            return diff >= 604800
        return True
    except:
        return True

@app.route("/scrape", methods=["POST"])
def scrape_flipkart():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"status": "error", "message": "Missing URL"}), 400

    title, price = scrape_price_and_title(url)
    return jsonify({"status": "success", "title": title, "price": price})

@app.route("/track", methods=["POST"])
def track_product():
    data = request.json
    url = data.get("url")
    min_price = data.get("min_price")
    max_price = data.get("max_price")
    frequency = data.get("frequency")
    alert_price = data.get("alert_price")

    if not all([url, min_price, max_price, frequency, alert_price]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    product_name, current_price = scrape_price_and_title(url)

    product = {
        "name": product_name,
        "url": url,
        "current_price": current_price,
        "min_price": min_price,
        "max_price": max_price,
        "frequency": frequency,
        "alert_price": alert_price,
        "last_checked": datetime.now().isoformat(),
        "price_history": [
            {"date": datetime.now().strftime("%Y-%m-%d"), "price": current_price}
        ],
    }

    products = []
    if os.path.exists("products.json"):
        with open("products.json", "r") as f:
            products = json.load(f)

    products.append(product)

    with open("products.json", "w") as f:
        json.dump(products, f, indent=4)

    return jsonify({"status": "success", "message": "Product tracked successfully"})

@app.route("/dashboard", methods=["GET"])
def get_dashboard_data():
    if os.path.exists("products.json"):
        with open("products.json", "r") as f:
            products = json.load(f)
    else:
        products = []

    for product in products:
        if should_scrape(product.get("last_checked", ""), product.get("frequency", "daily")):
            name, price = scrape_price_and_title(product["url"])
            product["name"] = name
            product["current_price"] = price
            product["price_history"].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "price": price
            })
            product["last_checked"] = datetime.now().isoformat()

    with open("products.json", "w") as f:
        json.dump(products, f, indent=4)

    return jsonify(products)

@app.route("/remove", methods=["POST"])
def remove_product():
    data = request.json
    url_to_remove = data.get("url")
    if not url_to_remove:
        return jsonify({"status": "error", "message": "Missing product URL"}), 400

    if os.path.exists("products.json"):
        with open("products.json", "r") as f:
            products = json.load(f)
        products = [p for p in products if p.get("url") != url_to_remove]
        with open("products.json", "w") as f:
            json.dump(products, f, indent=4)
        return jsonify({"status": "success", "message": "Product removed"})
    return jsonify({"status": "error", "message": "No products to remove"}), 404

@app.route("/alerts", methods=["GET", "POST"])
def alerts():
    if request.method == "GET":
        if os.path.exists("alerts.json"):
            with open("alerts.json", "r") as f:
                all_alerts = json.load(f)
        else:
            all_alerts = []
        return jsonify(all_alerts)

    data = request.json
    url = data.get("url")
    alert_price = data.get("alert_price")
    if not url or not alert_price:
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    alerts_list = []
    if os.path.exists("alerts.json"):
        with open("alerts.json", "r") as f:
            alerts_list = json.load(f)

    alerts_list.append({"url": url, "alert_price": alert_price})
    with open("alerts.json", "w") as f:
        json.dump(alerts_list, f, indent=4)

    return jsonify({"status": "success", "message": "Alert saved"})

@app.route("/product", methods=["GET"])
def get_product():
    import urllib.parse

    raw_url = request.args.get("url")
    if not raw_url:
        return jsonify({"status": "error", "message": "Missing url parameter"}), 400

    url = urllib.parse.unquote(raw_url)

    # Load products
    if not os.path.exists("products.json"):
        return jsonify({"status": "error", "message": "No products found"}), 404
    with open("products.json", "r") as f:
        products = json.load(f)

    # Find the product by URL
    index = next((i for i, p in enumerate(products) if p["url"] == url), -1)
    if index == -1:
        return jsonify({"status": "error", "message": "Product not found"}), 404

    product = products[index]

    # Scrape fresh price
    name, new_price = scrape_price_and_title(url)
    if new_price <= 0:
        # If scrape failed, return last-known state without appending bad data
        return jsonify(product)

    # Compute percentage change from last record (if any)
    last_entry = product["price_history"][-1]
    prev_price = last_entry["price"]
    pct_change = None
    try:
        pct_change = f"{((new_price - prev_price) / prev_price * 100):+.1f}%"
    except ZeroDivisionError:
        pct_change = None

    # Build new history entry
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "price": new_price
    }
    if pct_change is not None:
        entry["change"] = pct_change

    # Append and update
    product["name"] = name
    product["current_price"] = new_price
    product["price_history"].append(entry)
    product["last_checked"] = datetime.now().isoformat()

    # Persist full list back to file
    products[index] = product
    with open("products.json", "w") as f:
        json.dump(products, f, indent=4)

    return jsonify(product)





if __name__ == "__main__":
    app.run(debug=True)
