
from flask import Flask, render_template, request
from database.db import search_products, filter_products

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():

    products = []
    keyword = ""

    if request.method == "POST":

        keyword = request.form.get("keyword", "").strip()

        if keyword:
            products = search_products(keyword)

    return render_template(
        "index.html",
        products=products,
        keyword=keyword
    )


if __name__ == "__main__":
    app.run(debug=True)
