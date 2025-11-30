from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Vehicle, MaintenanceLog
import requests
from dotenv import load_dotenv
import os
import urllib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # required for sessions

# ---------- SQL Server (Docker) Connection ----------

# Get varibles from environment file
server = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")
username = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

db_params = urllib.parse.quote_plus(
    "Driver=ODBC Driver 18 for SQL Server;"
    f"Server={server},{port};"
    f"Database={database};"
    f"UID={username};"
    f"PWD={password};"
    "TrustServerCertificate=yes;"
)

DB_URL = f"mssql+pyodbc:///?odbc_connect={db_params}"

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


# Hardcoded user
USER_CRED = {"username": "admin", "password": "password"}

# ---------------- Login -----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == USER_CRED["username"] and password == USER_CRED["password"]:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- Dashboard -----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    session_db = SessionLocal()
    vehicles = session_db.query(Vehicle).all()
    session_db.close()

    return render_template("dashboard.html", user=session["user"], vehicles=vehicles)


# ---------------- Add Vehicle -----------------
# NHTSA API
NHTSA_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"

@app.route("/add_vehicle", methods=["GET", "POST"])
def add_vehicle_ui():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        vin = request.form.get("vin").strip().upper()
        if not vin:
            flash("VIN is required", "danger")
            return redirect(url_for("add_vehicle_ui"))

        # Get NHTSA VIN decode results
        try:
            r = requests.get(NHTSA_URL.format(vin=vin), timeout=10)
            data = r.json().get("Results", [])[0]
        except:
            flash("Unable to reach NHTSA VIN lookup service.", "danger")
            return redirect(url_for("add_vehicle_ui"))

        year = data.get("ModelYear")
        maker = data.get("Make")
        model = data.get("Model")

        # VALIDATION: All must be present
        if not year or not maker or not model:
            flash("Invalid or unrecognized VIN. Vehicle not added.", "danger")
            return redirect(url_for("add_vehicle_ui"))

        session_db = SessionLocal()

        # Avoid duplicate VIN entries
        existing = session_db.query(Vehicle).filter_by(vin=vin).first()
        if existing:
            flash(f"Vehicle {vin} already exists.", "info")
            session_db.close()
            return redirect(url_for("dashboard"))

        # Add new vehicle to DB
        vehicle = Vehicle(vin=vin, year=year, maker=maker, model=model)
        session_db.add(vehicle)
        session_db.commit()
        session_db.close()

        flash(f"Vehicle {vin} ({maker} {model} {year}) added successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_vehicle.html")


# ---------------- Add Maintenance -----------------
@app.route("/add_maintenance", methods=["GET", "POST"])
def add_maintenance_ui():
    if "user" not in session:
        return redirect(url_for("login"))

    session_db = SessionLocal()
    vehicles = session_db.query(Vehicle).all()
    if request.method == "POST":
        vin = request.form.get("vin")
        mileage = request.form.get("mileage")
        mtype = request.form.get("type")
        description = request.form.get("description", "")

        vehicle = session_db.query(Vehicle).filter_by(vin=vin).first()
        if not vehicle:
            flash("Vehicle not found", "danger")
        else:
            log = MaintenanceLog(vehicle_id=vehicle.id, mileage=int(mileage), type=mtype, description=description)
            session_db.add(log)
            session_db.commit()
            flash("Maintenance log added", "success")
        session_db.close()
        return redirect(url_for("dashboard"))

    session_db.close()
    return render_template("add_maintenance.html", vehicles=vehicles)

# ---------------- Maintenance Report -----------------
@app.route("/maintenance_report")
def maintenance_report_ui():
    if "user" not in session:
        return redirect(url_for("login"))

    session_db = SessionLocal()
    vehicles = session_db.query(Vehicle).all()
    vin_selected = request.args.get("vin")
    logs = []
    if vin_selected:
        vehicle = session_db.query(Vehicle).filter_by(vin=vin_selected).first()
        if vehicle:
            logs = session_db.query(MaintenanceLog).filter_by(vehicle_id=vehicle.id).order_by(MaintenanceLog.date_created.desc()).all()
    session_db.close()
    return render_template("maintenance_report.html", vehicles=vehicles, logs=logs, vin_selected=vin_selected)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)