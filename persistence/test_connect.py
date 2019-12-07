#!/usr/bin/env python3
# Test connection to the Skrate persistence database
import psycopg2

print("Trying to connect...")

eng = psycopg2.connect(host="localhost",
                       user="skrate_user",
                       password="skrate_password",
                       port="5432",
                       dbname="postgres")

print("Connected without error.")
