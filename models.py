from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4

db = SQLAlchemy()


def get_uuid():
    return uuid4().hex


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(100), primary_key=True, unique=True, default=get_uuid)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


class OtpRequests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    otp = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    time = db.Column(db.Integer, nullable=False)


class Expense(db.Model):
    id = db.Column(db.String(100), primary_key=True,
                   unique=True, default=get_uuid)
    email = db.Column(db.String(150), nullable=False)
    expense_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    tag = db.Column(db.String(50), nullable=False)
    mode = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
