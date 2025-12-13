from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Department(db.Model):
    __tablename__ = 'Department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    desc = db.Column(db.Text, nullable=True)
    doc_reg = db.relationship('Doctor', backref='department', lazy=True)

class Patient(db.Model):
    __tablename__ = 'Patient'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    med_history = db.Column(db.Text)
    phone = db.Column(db.String(20))
    is_blacklisted = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='patient_profile', uselist=False)

class Doctor(db.Model):
    __tablename__ = 'Doctor'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    bio = db.Column(db.Text)
    spec = db.Column(db.String(120), nullable=False)
    dept_id = db.Column(db.Integer, db.ForeignKey("Department.id"), nullable=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    user = db.relationship('User')
    dept = db.relationship("Department", overlaps="doc_reg")
    
    availability = db.relationship("Availability", backref="doctor", cascade="all, delete-orphan")

class Appointment(db.Model):
    __tablename__ = 'Appointment'
    id = db.Column(db.Integer, primary_key=True)
    pt_id = db.Column(db.Integer, db.ForeignKey("Patient.id"), nullable=False)
    doc_id = db.Column(db.Integer, db.ForeignKey("Doctor.id"), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False)

    patient = db.relationship("Patient", backref="appointments")
    doctor = db.relationship("Doctor", backref="appointments")

class Treatment(db.Model):
    __tablename__ = 'Treatment'
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.Integer, db.ForeignKey("Appointment.id"), nullable=False)
    diag = db.Column(db.Text, nullable=False)
    presc = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)

    app = db.relationship("Appointment", backref="treatments")

class Availability(db.Model):
    __tablename__ = 'Availability'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("Doctor.id"), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)