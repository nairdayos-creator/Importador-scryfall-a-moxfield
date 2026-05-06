from flask import Flask, render_template, request, Response
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

# ----------------------------
# FETCH CARDS
# ----------------------------
def fetch_all_cards(query):
    params = {
        "q": query,
        "unique": "cards",
        "format": "json"
    }

    url = BASE_URL

    while True:
        resp = requests.get(url, params=params)

        if resp.status_code == 404:
            return

        resp.raise_for_status()
        data = resp.json()

        for card in data.get("data", []):
            yield card

        if not data.get("has_more"):
            break

        url = data["next_page"]
        params = None
        time.sleep(0.2)


# ----------------------------
# CSV EXPORT (COLECCIÓN)
# ----------------------------
def generate_csv(query):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
    writer.writeheader()

    card_count = 0

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
        card_count += 1

    if card_count == 0:
        return None

    output.seek(0)
    return output


# ----------------------------
# TXT EXPORT (DECKLIST)
# ----------------------------
def generate_txt(query):
    lines = []
    card_count = 0

    for card in fetch_all_cards(query):
        name = card.get("name")
        if name:
            lines.append(f"1 {name}")
            card_count += 1

    if card_count == 0:
        return None

    return "\n".join(lines)


# ----------------------------
# ROUTE PRINCIPAL (CSV)
# ----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form.get("query", "").strip()

        if not query:
            return render_template(
                "index.html",
                error="Introduce una búsqueda"
            )

        csv_file = generate_csv(query)

        if csv_file is None:
            return render_template(
                "index.html",
                error="No se ha encontrado nada con esa búsqueda"
            )

        return Response(
            csv_file,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=moxfield_import.csv"
            }
        )

    return render_template("index.html")


# ----------------------------
# NUEVA RUTA TXT (DECKLIST)
# ----------------------------
@app.route("/txt", methods=["POST"])
def export_txt():
    query = request.form.get("query", "").strip()

    if not query:
        return render_template(
            "index.html",
            error="Introduce una búsqueda"
        )

    txt_data = generate_txt(query)

    if txt_data is None:
        return render_template(
            "index.html",
            error="No se ha encontrado nada con esa búsqueda"
        )

    return Response(
        txt_data,
        mimetype="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=decklist.txt"
        }
    )


# ----------------------------
# RUN (LOCAL ONLY)
# ----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
