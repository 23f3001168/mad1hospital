from flask import Flask, session, redirect, request, render_template
from datetime import datetime, timedelta
from sqlalchemy import cast, String
from models import db, Department, Doctor, Patient, User, Appointment, Treatment, Availability
import os

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-secret")
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "hospital.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(role="admin").first()
    if not admin:
        admin = User(username=os.environ.get("ADMIN_USER", "admin"),
             password=os.environ.get("ADMIN_PASS", "admin123"),
             role="admin")
        db.session.add(admin)
        db.session.commit()

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username=request.form.get("username")
        password=request.form.get("password")
        user=User.query.filter_by(username=username,password=password).first()
        if user:
            if not user.is_active:
                return render_template("index.html",msg="Account is blacklisted")
            session["user_id"]=user.id
            session["role"]=user.role
            if user.role=="admin":
                return redirect("/admin/dashboard")
            elif user.role=="doctor":
                return redirect("/doctor/dashboard")
            else:
                return redirect("/patient/dashboard")
        return render_template("index.html",msg="Invalid Credentials")
    return render_template("index.html")

@app.route("/login/doctor", methods=["GET", "POST"])
def login_doctor():
    if request.method=="POST":
        user=User.query.filter_by(username=request.form.get("username"),password=request.form.get("password"),role="doctor").first()
        if user:
            if not user.is_active:
                return render_template("login_doctor.html",msg="Account is blacklisted")
            session["user_id"]=user.id
            session["role"]="doctor"
            return redirect("/doctor/dashboard")
        return render_template("login_doctor.html",msg="Invalid Credentials")
    return render_template("login_doctor.html")

@app.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    if request.method=="POST":
        user=User.query.filter_by(username=request.form.get("username"),password=request.form.get("password"),role="admin").first()
        if user:
            if not user.is_active:
                return render_template("login_admin.html",msg="Account is blacklisted")
            session["user_id"]=user.id
            session["role"]="admin"
            return redirect("/admin/dashboard")
        return render_template("login_admin.html",msg="Invalid Credentials")
    return render_template("login_admin.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role")!="admin":
        return "Forbidden",403
    return render_template("admin_dashboard.html",
        total_depts=Department.query.count(),
        total_doctors=Doctor.query.count(),
        total_patients=Patient.query.count(),
        total_apps=Appointment.query.count()
    )

@app.route("/admin/appointments")
def admin_all_appointments():
    if session.get("role")!="admin":
        return "Forbidden",403
    apps=Appointment.query.order_by(Appointment.date,Appointment.time).all()
    return render_template("all_appointments.html",apps=apps)

@app.route("/admin/appointments/completed")
def admin_completed():
    if session.get("role")!="admin":
        return "Forbidden",403
    apps=Appointment.query.filter_by(status="Completed").order_by(Appointment.date,Appointment.time).all()
    return render_template("all_appointments.html",apps=apps)

@app.route("/dept/list")
def list_dept():
    if session.get("role")!="admin":
        return "Forbidden",403
    return render_template("list_dept.html",depts=Department.query.all())

@app.route("/dept/add",methods=["GET","POST"])
def add_dept():
    if session.get("role")!="admin":
        return "Forbidden",403
    if request.method=="POST":
        d=Department(name=request.form.get("dname"),desc=request.form.get("desc"))
        db.session.add(d)
        db.session.commit()
        return redirect("/dept/list")
    return render_template("add_dept.html")

@app.route("/dept/edit/<int:id>",methods=["GET","POST"])
def edit_dept(id):
    if session.get("role")!="admin":
        return "Forbidden",403
    dept=Department.query.get(id)
    if request.method=="POST":
        dept.name=request.form.get("dname")
        dept.desc=request.form.get("desc")
        db.session.commit()
        return redirect("/dept/list")
    return render_template("edit_dept.html",dept=dept)

@app.route("/dept/delete/<int:id>")
def delete_dept(id):
    if session.get("role")!="admin":
        return "Forbidden",403
    db.session.delete(Department.query.get(id))
    db.session.commit()
    return redirect("/dept/list")

@app.route("/doctor/list")
def list_doc():
    if session.get("role")!="admin":
        return "Forbidden",403
    q=request.args.get("q","").strip()
    if q:
        docs=(Doctor.query.join(User,Doctor.user_id==User.id)
            .join(Department,Doctor.dept_id==Department.id)
            .filter(
                User.fname.ilike(f"%{q}%") |
                User.lname.ilike(f"%{q}%") |
                User.username.ilike(f"%{q}%") |
                Doctor.spec.ilike(f"%{q}%") |
                Department.name.ilike(f"%{q}%") |
                cast(User.id,String).ilike(f"%{q}%")
            ).all())
    else:
        docs=Doctor.query.all()
    return render_template("list_doc.html",docs=docs,q=q)

@app.route("/doctor/add",methods=["GET","POST"])
def add_doc():
    if session.get("role")!="admin":
        return "Forbidden",403
    if request.method=="POST":
        user=User(username=request.form.get("username"),password=request.form.get("password"),
                  role="doctor",fname=request.form.get("fname"),lname=request.form.get("lname"))
        db.session.add(user)
        db.session.commit()
        doc=Doctor(user_id=user.id,spec=request.form.get("spec"),
                   dept_id=request.form.get("dept_id"),bio=request.form.get("bio"))
        db.session.add(doc)
        db.session.commit()
        return redirect("/doctor/list")
    return render_template("add_doc.html",depts=Department.query.all())

@app.route("/doctor/edit/<int:id>",methods=["GET","POST"])
def edit_doc(id):
    if session.get("role")!="admin":
        return "Forbidden",403
    doc=Doctor.query.get(id)
    usr=User.query.get(doc.user_id)
    if request.method=="POST":
        usr.fname=request.form.get("fname")
        usr.lname=request.form.get("lname")
        usr.username=request.form.get("username")
        usr.password=request.form.get("password")
        doc.spec=request.form.get("spec")
        doc.dept_id=request.form.get("dept_id")
        doc.bio=request.form.get("bio")
        db.session.commit()
        return redirect("/doctor/list")
    return render_template("edit_doc.html",doc=doc,usr=usr,depts=Department.query.all())

@app.route("/doctor/delete/<int:id>")
def del_doc(id):
    if session.get("role")!="admin":
        return "Forbidden",403
    doc=Doctor.query.get(id)
    user=User.query.get(doc.user_id)
    db.session.delete(doc)
    db.session.delete(user)
    db.session.commit()
    return redirect("/doctor/list")

@app.route("/patient/register",methods=["GET","POST"])
def patient_register():
    if request.method=="POST":
        user=User(username=request.form.get("username"),
                  password=request.form.get("password"),
                  role="patient",
                  fname=request.form.get("fname"),
                  lname=request.form.get("lname"))
        db.session.add(user)
        db.session.commit()
        patient=Patient(user_id=user.id,age=request.form.get("age"),
                        gender=request.form.get("gender"),
                        med_history=request.form.get("med_history"),
                        phone=request.form.get("phone"))
        db.session.add(patient)
        db.session.commit()
        return redirect("/login")
    return render_template("patient_register.html")

@app.route("/patient/dashboard")
def patient_dashboard():
    if session.get("role")!="patient":
        return "Forbidden",403
    patient=Patient.query.filter_by(user_id=session.get("user_id")).first()
    depts=Department.query.all()
    availability=Availability.query.join(Doctor,Availability.doctor_id==Doctor.id).all()
    apps=Appointment.query.filter_by(pt_id=patient.id).order_by(Appointment.date,Appointment.time).all()
    treatments=Treatment.query.all()
    return render_template("patient_dashboard.html",
                           patient=patient,depts=depts,
                           availability=availability,
                           apps=apps,treatments=treatments)

@app.route("/patient/list")
def list_patient():
    if session.get("role")!="admin":
        return "Forbidden",403
    q=request.args.get("q","").strip()
    if q:
        patients=(Patient.query.join(User,Patient.user_id==User.id)
                  .filter(
                      User.fname.ilike(f"%{q}%") |
                      User.lname.ilike(f"%{q}%") |
                      cast(Patient.id,String).ilike(f"%{q}%") |
                      Patient.phone.ilike(f"%{q}%")
                  ).all())
    else:
        patients=Patient.query.all()
    return render_template("list_patient.html",patients=patients,q=q)

@app.route("/patient/edit",methods=["GET","POST"])
def edit_patient():
    if session.get("role")!="patient":
        return "Forbidden",403
    patient=Patient.query.filter_by(user_id=session.get("user_id")).first()
    if request.method=="POST":
        patient.age=request.form.get("age")
        patient.gender=request.form.get("gender")
        patient.med_history=request.form.get("med_history")
        patient.phone=request.form.get("phone")
        db.session.commit()
        return redirect("/patient/dashboard")
    return render_template("edit_patient.html",patient=patient)

@app.route("/patient/delete/<int:id>")
def delete_patient(id):
    if session.get("role")!="admin":
        return "Forbidden",403
    pat=Patient.query.get(id)
    user=User.query.get(pat.user_id)
    db.session.delete(pat)
    db.session.delete(user)
    db.session.commit()
    return redirect("/patient/list")

@app.route("/appointment/book",methods=["GET","POST"])
def book():
    if session.get("role")!="patient":
        return "Forbidden",403
    patient=Patient.query.filter_by(user_id=session.get("user_id")).first()
    if request.method=="POST":
        doc_id=request.form.get("doc_id")
        doctor=Doctor.query.get(doc_id)
        if doctor.is_blacklisted:
            return render_template("book_appointment.html",
                msg="Doctor is blacklisted and unavailable for appointments",
                doctors=Doctor.query.all(),
                depts=Department.query.all())
        date=request.form.get("date")
        time=request.form.get("time")
        exists=Appointment.query.filter_by(doc_id=doc_id,date=date,time=time).first()
        if exists:
            return render_template("book_appointment.html",
                msg="Slot Not Available",
                doctors=Doctor.query.all(),
                depts=Department.query.all())
        ap=Appointment(pt_id=patient.id,doc_id=doc_id,date=date,time=time,status="Booked")
        db.session.add(ap)
        db.session.commit()
        return redirect("/patient/appointments")
    return render_template("book_appointment.html",
                           doctors=Doctor.query.all(),
                           depts=Department.query.all())

@app.route("/patient/appointments")
def patient_appointments():
    if session.get("role")!="patient":
        return "Forbidden",403
    pat=Patient.query.filter_by(user_id=session.get("user_id")).first()
    apps=Appointment.query.filter_by(pt_id=pat.id).order_by(Appointment.date,Appointment.time).all()
    treatments=Treatment.query.all()
    return render_template("patient_appointments.html",apps=apps,treatments=treatments)

@app.route("/patient/appointments/cancel/<int:id>")
def cancel_app(id):
    if session.get("role")!="patient":
        return "Forbidden",403
    pat=Patient.query.filter_by(user_id=session.get("user_id")).first()
    app=Appointment.query.get(id)
    if app.pt_id!=pat.id:
        return "Forbidden",403
    app.status="Cancelled"
    db.session.commit()
    return redirect("/patient/appointments")

@app.route("/doctor/dashboard")
def doctor_dashboard():
    if session.get("role")!="doctor":
        return "Forbidden",403
    doctor=Doctor.query.filter_by(user_id=session.get("user_id")).first()
    apps=Appointment.query.filter_by(doc_id=doctor.id).all()
    today=datetime.today().date()
    week_end=today+timedelta(days=7)
    upcoming=[]
    for a in apps:
        try:
            d=datetime.strptime(a.date,"%Y-%m-%d").date()
            if today<=d<=week_end:
                upcoming.append(a)
        except:
            pass
    pids={a.pt_id for a in apps}
    assigned=Patient.query.filter(Patient.id.in_(pids)).all()
    return render_template("doctor_dashboard.html",
                           doctor=doctor,upcoming_appointments=upcoming,
                           assigned_patients=assigned)

@app.route("/doctor/appointments")
def doctor_appointments():
    if session.get("role")!="doctor":
        return "Forbidden",403
    doctor=Doctor.query.filter_by(user_id=session.get("user_id")).first()
    apps=Appointment.query.filter_by(doc_id=doctor.id).order_by(Appointment.date,Appointment.time).all()
    return render_template("doctor_appointments.html",apps=apps)

@app.route("/doctor/cancel/<int:id>")
def doctor_cancel(id):
    if session.get("role")!="doctor":
        return "Forbidden",403
    doctor=Doctor.query.filter_by(user_id=session.get("user_id")).first()
    app=Appointment.query.get(id)
    if app.doc_id!=doctor.id:
        return "Forbidden",403
    app.status="Cancelled"
    db.session.commit()
    return redirect("/doctor/appointments")

@app.route("/doctor/availability",methods=["POST"])
def doctor_availability():
    if session.get("role")!="doctor":
        return "Forbidden",403
    doctor=Doctor.query.filter_by(user_id=session.get("user_id")).first()
    date=request.form.get("date")
    slots=request.form.get("slots")
    if not date or not slots:
        return redirect("/doctor/dashboard")
    for s in [i.strip() for i in slots.split(",") if i.strip()]:
        try:
            start,end=s.split("-")
        except:
            start=s
            end=s
        av=Availability(doctor_id=doctor.id,date=date,start_time=start,end_time=end)
        db.session.add(av)
    db.session.commit()
    return redirect("/doctor/dashboard")

@app.route("/doctor/patient/history/<int:pid>")
def doctor_history(pid):
    if session.get("role")!="doctor":
        return "Forbidden",403
    doctor=Doctor.query.filter_by(user_id=session.get("user_id")).first()
    patient=Patient.query.get(pid)
    apps=Appointment.query.filter_by(doc_id=doctor.id,pt_id=patient.id).all()
    treatments=Treatment.query.all()
    return render_template("doctor_patient_history.html",
                           patient=patient,apps=apps,treatments=treatments)

@app.route("/treatment/add/<int:app_id>",methods=["GET","POST"])
def add_treatment(app_id):
    if session.get("role")!="doctor":
        return "Forbidden",403
    app_obj=Appointment.query.get(app_id)
    doctor=Doctor.query.filter_by(user_id=session.get("user_id")).first()
    if app_obj.doc_id!=doctor.id:
        return "Forbidden",403
    if request.method=="POST":
        t=Treatment(app_id=app_id,diag=request.form.get("diag"),
                    presc=request.form.get("presc"),
                    notes=request.form.get("notes"))
        db.session.add(t)
        app_obj.status="Completed"
        db.session.commit()
        return redirect("/doctor/appointments")
    return render_template("add_treatment.html",app=app_obj)

@app.route("/admin/patient/edit/<int:id>",methods=["GET","POST"])
def admin_edit_patient(id):
    if session.get("role")!="admin":
        return "Forbidden",403
    patient=Patient.query.get(id)
    user=User.query.get(patient.user_id)
    if request.method=="POST":
        user.fname=request.form.get("fname")
        user.lname=request.form.get("lname")
        patient.age=request.form.get("age")
        patient.gender=request.form.get("gender")
        patient.phone=request.form.get("phone")
        patient.med_history=request.form.get("med_history")
        db.session.commit()
        return redirect("/patient/list")
    return render_template("admin_edit_patient.html",patient=patient,user=user)

@app.route("/admin/blacklist/doctor/<int:id>")
def admin_blacklist_doctor(id):
    if session.get("role")!="admin":
        return "Forbidden",403
    doc=Doctor.query.get(id)
    if not doc:
        return "Not found",404
    doc.is_blacklisted=True
    doc.user.is_active=False
    db.session.commit()
    return redirect("/doctor/list")

@app.route("/admin/blacklist/patient/<int:id>")
def admin_blacklist_patient(id):
    if session.get("role")!="admin":
        return "Forbidden",403
    pat=Patient.query.get(id)
    if not pat:
        return "Not found",404
    pat.is_blacklisted=True
    pat.user.is_active=False
    db.session.commit()
    return redirect("/patient/list")

if __name__=="__main__":
    app.run(debug=True)
