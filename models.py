from database import db
from flask_login import UserMixin

# Admin user
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Students table
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(20), nullable=False)

# Result table
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    marks = db.Column(db.Integer, nullable=False)
