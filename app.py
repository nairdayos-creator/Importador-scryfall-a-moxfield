from flask import Flask, render_template, request, send_file, Response
import requests
import csv
import time
import io

app = Flask(__name__)

BASE_URL = "https://api.scryfall.com/cards/search"

FIELDNAMES = [
    "Count",
    "Tradelist Count",
    "Name",
    "Edition",
    "Condition",
    "Language",
    "Foil",
    "Tags",
    "Last Modified",
    "Collector Number",
    "Alter",
    "Proxy",
    "Purchase Price"
]

def fetch_all_cards(query):
    params = {
        "q": query,
        "unique": "cards",
        "format": "json"
    }
    url = BASE_URL

    while True:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        for card in data.get("data", []):
            yield card

        if not data.get("has_more"):
            break

        url = data["next_page"]
        params = None
        time.sleep(0.2)


def generate_csv(query):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
    writer.writeheader()

    for card in fetch_all_cards(query):
        writer.writerow({
            "Count": 1,
            "Tradelist Count": "",
            "Name": card.get("name"),
            "Edition": card.get("set"),
            "Condition": "",
            "Language": card.get("lang"),
            "Foil": "Yes" if card.get("foil") else "No",
            "Tags": "",
            "Last Modified": "",
            "Collector Number": card.get("collector_number"),
            "Alter": "",
            "Proxy": "",
            "Purchase Price": ""
        })

    output.seek(0)
    return output


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form.get("query")

        if not query:
            return render_template("index.html", error="Introduce una búsqueda")

        csv_file = generate_csv(query)

        return Response(
            csv_file,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=moxfield_import.csv"
            }
        )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
