from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Vehicle, MaintenanceLog
import requests
from dotenv import load_dotenv
import os
import urllib

# NHTSA API
NHTSA_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")  # required for sessions

# DB_URL = (
#     "mssql+pyodbc://sa:Password1@auto-track.citccaogqub3.us-east-1.rds.amazonaws.com:1433/CarMaintenanceDB"
#     "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
# )

# ---------- SQL Server (Docker) Connection ----------

db_params = urllib.parse.quote_plus(
    "Driver=ODBC Driver 18 for SQL Server;"
    "Server=localhost,1433;"
    "Database=CarMaintenanceDB;"
    "UID=sa;"
    "PWD=Password1@;"
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
