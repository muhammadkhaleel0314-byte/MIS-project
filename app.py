from flask import Flask, render_template, request, session, redirect, url_for, send_file
import pandas as pd
from io import BytesIO

app = Flask(__name__)
app.secret_key = "secret123"

# ================= Login =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if u == "admin" and p == "admin123":
            session["user"] = u
            return redirect(url_for("dashboard"))
    return render_template("login.html")

# ================= Dashboard =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# ================= Sustainability =================
@app.route("/sustainability")
def sustainability():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("sustainability.html")

# ================= BOP =================
BOP_DATA = []  # store current uploaded BOP

@app.route("/bop")
def bop():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("bop.html")

@app.route("/upload_bop", methods=["POST"])
def upload_bop():
    global BOP_DATA
    file = request.files.get("file")
    if not file:
        return {"status":"error","message":"No file uploaded"}, 400
    df = pd.read_excel(file)
    expected_cols = ["Name","CNIC","Account No","Bank BR Code","Bank BR Name"]
    df = df[expected_cols]
    BOP_DATA = df.to_dict(orient="records")
    return {"status":"success","data":BOP_DATA}

@app.route("/search_bop", methods=["POST"])
def search_bop():
    global BOP_DATA
    cnic = request.json.get("cnic","").strip()
    if not cnic:
        return {"status":"success","data":BOP_DATA}
    filtered = [row for row in BOP_DATA if cnic in str(row["CNIC"])]
    return {"status":"success","data":filtered}

@app.route("/download_bop_excel")
def download_bop_excel():
    global BOP_DATA
    df = pd.DataFrame(BOP_DATA)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(output, download_name="BOP.xlsx", as_attachment=True)

# ================= Logout =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session

UPLOAD_FOLDER = "uploads"
BOP_FILE = os.path.join(UPLOAD_FOLDER, "bop.xlsx")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/bop", methods=["GET", "POST"])
def bop():
    if "user" not in session:
        return redirect(url_for("login"))

    data = []
    cnic_search = ""

    # Excel upload
    if request.method == "POST":
        if "file" in request.files:
            file = request.files["file"]
            if file.filename != "":
                file.save(BOP_FILE)

        cnic_search = request.form.get("cnic", "").strip()

    # Read saved Excel (even after relogin)
    if os.path.exists(BOP_FILE):
        df = pd.read_excel(BOP_FILE, dtype=str)
        df = df.fillna("")

        if cnic_search:
            df = df[df["CNIC"] == cnic_search]

        data = df.to_dict(orient="records")

    return render_template("bop.html", data=data)