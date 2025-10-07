#!/usr/bin/env python3
"""
Server entry point for production deployment
This file imports the app from clean_healthcare_app.py
"""
from clean_healthcare_app import app

if __name__ == "__main__":
    app.run()
