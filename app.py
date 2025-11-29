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