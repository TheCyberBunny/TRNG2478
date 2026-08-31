"""
Robopulse Command Center
Day 5 - password hashing and JWT helper functions

SECRET_KEY: it follows the same env-var-with-fallback pattern that we saw on Day 3's
DATABASE_URL. Note, we will not be committing a real secret key here if this were
a real project being pushed to production(NOT SECURE).
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

#Security Constants and helper functions for password hashing and JWT token management
SECRET_KEY = os.environ.get("SECRET_KEY", "<replace-with-a-real-secret-key>")

#defines our algorithm for signing the JWT(JSON-Web Tokens) Tokens. There are many algorithms
#to choose from, we will be using HS256 (this is a common choice for symmetric signing)
ALGORITHM = "HS256"

#the expiration time for access tokens, in minutes
ACCESS_TOKEN_EXPIRE_MINUTES = 30

#We need 2 different functions for password hashing and verification to make sure we are NEVER
#storing plain text passwords in the db. Instead, we store the hashed version of the password,
#which is a one-way transformation that cannot be easily reversed

#takes a plain text password as an input, hashes it using bcrypt, and returns the hashed pw as
#a string
def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

#takes a hashed password and a plain text passwrod as input, and checks if the plain text password
#matches the hashed password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


#This function creates a JWT access token with the provided data and an optional expiration time
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    #to_encode is a copy of the input data dictionary, which will be used to create the payload of the JWT
    to_encode = data.copy()

    #check if an expiration time provided; if not, we can use the default expiration time defined by
    #ACCESS_TOKEN_EXPIRE_MINUTES.
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#this function decodes a JWT access token and returns the payload as a dictionary
def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])