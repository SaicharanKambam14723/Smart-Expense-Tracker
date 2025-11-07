from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
import pandas as pd
import json

from config import UPLOAD_FOLDER
from models.database import init_db, get_db
from utils.ocr import extract_text, parse_fields


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "dev"  # for flash messages

init_db()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"png", "jpg", "jpeg"}


def yyyymm_today():
    return datetime.now().strftime("%Y-%m")


@app.route("/")
def index():
    # filters (optional)
    category = request.args.get('category', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    conn = get_db()
    c = conn.cursor()

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC"
    c.execute(query, params)
    expenses = c.fetchall()

    c.execute("SELECT SUM(amount) FROM expenses")
    total = c.fetchone()[0] or 0

    # current month spending + budget
    current_month = yyyymm_today()
    c.execute("SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', date)=?", (current_month,))
    month_spent = c.fetchone()[0] or 0

    c.execute("SELECT amount FROM budget WHERE month=?", (current_month,))
    row = c.fetchone()
    month_budget = row[0] if row else None

    over_budget = month_budget is not None and month_spent > month_budget

    conn.close()

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        month_spent=month_spent,
        month_budget=month_budget,
        over_budget=over_budget
    )


# ADD EXPENSE
@app.route("/add", methods=["POST"])
def add_expense():
    amount = request.form["amount"]
    category = request.form["category"]
    description = request.form.get("description", "")
    date = request.form["date"] or datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO expenses(amount,category,description,date) VALUES(?,?,?,?)",
        (amount, category, description, date),
    )
    conn.commit()
    conn.close()
    return redirect("/")


# DELETE
@app.route("/delete/<int:id>")
def delete_expense(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


# EDIT
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_expense(id):
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        description = request.form.get("description", "")
        date = request.form["date"]
        c.execute(
            "UPDATE expenses SET amount=?,category=?,description=?,date=? WHERE id=?",
            (amount, category, description, date, id),
        )
        conn.commit()
        conn.close()
        return redirect("/")

    c.execute("SELECT * FROM expenses WHERE id=?", (id,))
    expense = c.fetchone()
    conn.close()
    return render_template("edit.html", expense=expense)


# UPLOAD RECEIPT + OCR
@app.route("/upload", methods=["GET", "POST"])
def upload_receipt():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file uploaded")
            return redirect(request.url)

        file = request.files["file"]
        if not file or file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            txt = extract_text(filepath)
            amount, date = parse_fields(txt)

            return render_template(
                "upload_receipt.html",
                extracted_text=txt,
                amount=amount,
                date=date,
                filename=os.path.basename(filepath)
            )

        flash("Unsupported file type")
        return redirect(request.url)

    return render_template("upload_receipt.html")


# REPORTS (tables + JSON for charts)
@app.route("/reports")
def reports():
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()

    if df.empty:
        monthly = []
        category = []
    else:
        df["month"] = df["date"].str[:7]
        monthly = df.groupby("month")["amount"].sum().reset_index().to_dict("records")
        category = df.groupby("category")["amount"].sum().reset_index().to_dict("records")

    return render_template(
        "reports.html",
        monthly=monthly,
        category=category,
        monthly_json=json.dumps(monthly),
        category_json=json.dumps(category)
    )


# STATS (Chart.js demo page)
@app.route("/stats")
def stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    category_data = [{"category": r[0], "amount": r[1]} for r in c.fetchall()]
    c.execute("SELECT strftime('%Y-%m', date) as m, SUM(amount) FROM expenses GROUP BY m")
    month_data = [{"month": r[0], "amount": r[1]} for r in c.fetchall()]
    conn.close()
    return render_template("stats.html", category_data=json.dumps(category_data), month_data=json.dumps(month_data))


# BUDGET: set/get for a month (YYYY-MM)
@app.route("/budget", methods=["GET", "POST"])
def budget():
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        month = request.form.get("month") or yyyymm_today()
        amount = float(request.form.get("amount", 0))
        # upsert
        c.execute("INSERT INTO budget(month, amount) VALUES(?, ?) ON CONFLICT(month) DO UPDATE SET amount=excluded.amount",
                  (month, amount))
        conn.commit()
        conn.close()
        flash(f"Budget for {month} set to {amount}")
        return redirect(url_for("index"))

    # GET: list budgets
    c.execute("SELECT month, amount FROM budget ORDER BY month DESC")
    rows = c.fetchall()
    conn.close()
    return render_template("budget.html", budgets=rows)


if __name__ == "__main__":
    app.run(debug=True)