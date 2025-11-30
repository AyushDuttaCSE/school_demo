from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length
from config import Config
import os
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "admin_login"

# -----------------------
# Models
# -----------------------
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(150), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Admission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(200), nullable=False)
    student_class = db.Column(db.String(50))
    age = db.Column(db.Integer)
    parent_email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------
# Forms
# -----------------------
class AdmissionForm(FlaskForm):
    student_name = StringField("Student Name", validators=[DataRequired(), Length(max=200)])
    student_class = StringField("Class (e.g., Class 9)", validators=[DataRequired()])
    age = IntegerField("Age", validators=[DataRequired()])
    parent_email = StringField("Parent Email", validators=[Email(), Length(max=150)])
    phone = StringField("Phone", validators=[Length(max=50)])
    message = TextAreaField("Additional info")
    submit = SubmitField("Submit Application")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

# -----------------------
# Login loader
# -----------------------
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# -----------------------
# Routes
# -----------------------
@app.route("/")
def index():
    notices = Notice.query.order_by(Notice.date.desc()).limit(5).all()
    return render_template("index.html", notices=notices)

@app.route("/admission", methods=["GET", "POST"])
def admission():
    form = AdmissionForm()
    if form.validate_on_submit():
        new = Admission(
            student_name=form.student_name.data,
            student_class=form.student_class.data,
            age=form.age.data,
            parent_email=form.parent_email.data,
            phone=form.phone.data,
            message=form.message.data
        )
        db.session.add(new)
        db.session.commit()
        flash("Application submitted. We will contact you soon.", "success")
        return redirect(url_for("admission"))
    return render_template("admission.html", form=form)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            flash("Logged in successfully", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("admin_login.html", form=form)

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    admissions = Admission.query.order_by(Admission.submitted_at.desc()).limit(50).all()
    notices = Notice.query.order_by(Notice.date.desc()).all()
    return render_template("admin_dashboard.html", admissions=admissions, notices=notices)

@app.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("admin_login"))

# Simple route to add a notice (in production make a proper form + check rights)
@app.route("/admin/add_notice", methods=["POST"])
@login_required
def add_notice():
    title = request.form.get("title")
    content = request.form.get("content")
    if title and content:
        n = Notice(title=title, content=content)
        db.session.add(n)
        db.session.commit()
        flash("Notice added", "success")
    return redirect(url_for("admin_dashboard"))

# Serve uploaded files (if you allow uploads)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -----------------------
# CLI helper: create admin if none exists
# -----------------------
@app.cli.command("create-admin")
def create_admin():
    """Create an admin user (run: flask create-admin)"""
    import getpass
    email = input("Admin email: ").strip()
    name = input("Admin name: ").strip()
    password = getpass.getpass("Password: ")
    if not email or not password:
        print("Email and password are required")
        return
    if Admin.query.filter_by(email=email).first():
        print("Admin already exists")
        return
    admin = Admin(email=email, name=name)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print("Admin created.")

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
