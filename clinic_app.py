import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import uuid
from DB.neo_connection import run_query
# Patients
def create_patient(pid, name, dob, address, phone):
    cypher = """
    MERGE (p:Patient {patient_id:$pid})
    SET p.name=$name, p.dob=$dob, p.address=$addr, p.phone=$phone
    """
    run_query(cypher, {"pid": int(pid), "name": name, "dob": dob, "addr": address, "phone": phone})

def list_patients():
    rows = run_query("MATCH (p:Patient) RETURN p.patient_id AS id, p.name AS name, p.dob AS dob, p.phone AS phone ORDER BY p.patient_id")
    return rows

# Doctors
def create_doctor(did, name, specialty, phone):
    cypher = "MERGE (d:Doctor {doctor_id:$did}) SET d.name=$name, d.specialty=$spec, d.phone=$phone"
    run_query(cypher, {"did": int(did), "name": name, "spec": specialty, "phone": phone})

def list_doctors():
    return run_query("MATCH (d:Doctor) RETURN d.doctor_id AS id, d.name AS name, d.specialty AS spec ORDER BY d.doctor_id")

# Appointments
def create_appointment(aid, date, time, doctor_id, patient_id):
    cypher = """
    MERGE (a:Appointment {appt_id:$aid})
    SET a.date=$date, a.time=$time
    WITH a
    MATCH (d:Doctor {doctor_id:$did}), (p:Patient {patient_id:$pid})
    MERGE (d)-[:HAS_APPOINTMENT]->(a)
    MERGE (p)-[:HAS_APPOINTMENT]->(a)
    """
    run_query(cypher, {"aid": int(aid), "date": date, "time": time, "did": int(doctor_id), "pid": int(patient_id)})

def list_appointments():
    cypher = """
    MATCH (d:Doctor)-[:HAS_APPOINTMENT]->(a:Appointment)<-[:HAS_APPOINTMENT]-(p:Patient)
    RETURN a.appt_id AS id, a.date AS date, a.time AS time, d.name AS doctor, p.name AS patient
    ORDER BY a.date, a.time
    """
    return run_query(cypher)

# Messages (simple graph: User nodes + Message nodes)
def send_message(sender_id, receiver_id, text, image_path=None):
    mid = uuid.uuid4().hex
    ts = datetime.utcnow().isoformat()
    cypher = """
    MERGE (s:User {id:$sid})
    MERGE (r:User {id:$rid})
    CREATE (m:Message {mid:$mid, text:$text, image_path:$img, timestamp:$ts})
    CREATE (s)-[:SENT]->(m)-[:RECEIVED_BY]->(r)
    RETURN m.mid AS mid, m.text AS text, m.image_path AS img, m.timestamp AS ts, s.id AS sender, r.id AS receiver
    """
    recs = run_query(cypher, {"sid": str(sender_id), "rid": str(receiver_id), "mid": mid, "text": text, "img": image_path, "ts": ts})
    return recs[0] if recs else None

def get_conversation(u1, u2):
    cypher = """
    MATCH (s:User)-[:SENT]->(m:Message)-[:RECEIVED_BY]->(r:User)
    WHERE (s.id=$u1 AND r.id=$u2) OR (s.id=$u2 AND r.id=$u1)
    RETURN m.mid AS mid, m.text AS text, m.image_path AS img, m.timestamp AS ts, s.id AS sender, r.id AS receiver
    ORDER BY m.timestamp
    """
    return run_query(cypher, {"u1": str(u1), "u2": str(u2)})

#UI

def launch_gui():
    root = tk.Tk()
    root.title("Clinic")
    root.geometry("820x520")

    frame = tk.Frame(root); frame.pack(pady=10)

    tk.Label(frame, text="Clinic (Neo4j) — Simple demo", font=("Arial", 14)).grid(row=0, columnspan=5, pady=6)

    # Buttons to open small windows
    tk.Button(frame, text="Patients", width=14, command=lambda: patient_window(root)).grid(row=1, column=0, padx=6, pady=6)
    tk.Button(frame, text="Doctors", width=14, command=lambda: doctor_window(root)).grid(row=1, column=1, padx=6, pady=6)
    tk.Button(frame, text="Appointments", width=14, command=lambda: appointment_window(root)).grid(row=1, column=2, padx=6, pady=6)
    tk.Button(frame, text="Messages", width=14, command=lambda: message_window(root)).grid(row=1, column=3, padx=6, pady=6)
    tk.Button(frame, text="Search", width=14, command=lambda: search_window(root)).grid(row=1, column=4, padx=6, pady=6)

    root.mainloop()

# Windows
def patient_window(parent):
    win = tk.Toplevel(parent); win.title("Patients"); win.geometry("520x420")
    frm = tk.Frame(win); frm.pack(pady=8)
    labels = ["ID","Name","DOB (YYYY-MM-DD)","Address","Phone"]; entries=[]
    for i,l in enumerate(labels):
        tk.Label(frm,text=l).grid(row=i,column=0,sticky="e")
        e=tk.Entry(frm,width=36); e.grid(row=i,column=1,padx=6,pady=3); entries.append(e)
    def save():
        try:
            create_patient(int(entries[0].get()), entries[1].get(), entries[2].get(), entries[3].get(), entries[4].get())
            messagebox.showinfo("OK","Patient saved"); refresh()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
    tk.Button(win,text="Save",command=save).pack(pady=6)
    box = tk.Listbox(win,width=72); box.pack(padx=10,pady=6,fill="both",expand=True)
    def refresh():
        box.delete(0,tk.END)
        for r in list_patients():
            box.insert(tk.END, f"#{r['id']} | {r['name']} | DOB:{r['dob']} | {r['phone']}")
    refresh()

def doctor_window(parent):
    win = tk.Toplevel(parent); win.title("Doctors"); win.geometry("520x380")
    frm = tk.Frame(win); frm.pack(pady=8)
    labels = ["ID","Name","Specialty","Phone"]; entries=[]
    for i,l in enumerate(labels):
        tk.Label(frm,text=l).grid(row=i,column=0,sticky="e")
        e=tk.Entry(frm,width=36); e.grid(row=i,column=1,padx=6,pady=3); entries.append(e)
    def save():
        try:
            create_doctor(int(entries[0].get()), entries[1].get(), entries[2].get(), entries[3].get())
            messagebox.showinfo("OK","Doctor saved"); refresh()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
    tk.Button(win,text="Save",command=save).pack(pady=6)
    box = tk.Listbox(win,width=72); box.pack(padx=10,pady=6,fill="both",expand=True)
    def refresh():
        box.delete(0,tk.END)
        for r in list_doctors():
            box.insert(tk.END, f"#{r['id']} | {r['name']} | {r['spec']}")
    refresh()

def appointment_window(parent):
    win = tk.Toplevel(parent); win.title("Appointments"); win.geometry("760x440")
    frm = tk.Frame(win); frm.pack(pady=6)
    tk.Label(frm,text="ApptID").grid(row=0,column=0); e_id=tk.Entry(frm); e_id.grid(row=0,column=1)
    tk.Label(frm,text="Date YYYY-MM-DD").grid(row=1,column=0); e_date=tk.Entry(frm); e_date.grid(row=1,column=1)
    tk.Label(frm,text="Time HH:MM:SS").grid(row=2,column=0); e_time=tk.Entry(frm); e_time.grid(row=2,column=1)
    tk.Label(frm,text="Doctor ID").grid(row=3,column=0); e_doc=tk.Entry(frm); e_doc.grid(row=3,column=1)
    tk.Label(frm,text="Patient ID").grid(row=4,column=0); e_pat=tk.Entry(frm); e_pat.grid(row=4,column=1)
    def save():
        try:
            create_appointment(int(e_id.get()), e_date.get(), e_time.get(), int(e_doc.get()), int(e_pat.get()))
            messagebox.showinfo("OK","Appointment created"); refresh()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
    tk.Button(win,text="Save Appointment",command=save).pack(pady=6)
    box = tk.Listbox(win,width=110); box.pack(padx=10,pady=6,fill="both",expand=True)
    def refresh():
        box.delete(0,tk.END)
        for r in list_appointments():
            box.insert(tk.END, f"#{r['id']} | {r['date']} {r['time']} | Dr:{r['doctor']} with {r['patient']}")
    refresh()

def message_window(parent):
    # For demo: use two ids you type in (no login). Simple send/list.
    win = tk.Toplevel(parent); win.title("Messages"); win.geometry("760x520")
    top = tk.Frame(win); top.pack(pady=6)
    tk.Label(top,text="Sender ID").grid(row=0,column=0); e_sender=tk.Entry(top); e_sender.grid(row=0,column=1)
    tk.Label(top,text="Receiver ID").grid(row=0,column=2); e_receiver=tk.Entry(top); e_receiver.grid(row=0,column=3)
    box = tk.Listbox(win,width=110,height=18); box.pack(padx=10,pady=6,fill="both",expand=True)
    bottom = tk.Frame(win); bottom.pack(fill="x",padx=10,pady=6)
    entry = tk.Entry(bottom,width=70); entry.pack(side="left",padx=(0,6))
    img_var = tk.StringVar()
    def browse():
        p = filedialog.askopenfilename()
        if p: img_var.set(p); messagebox.showinfo("Attached", p)
    def do_send():
        s = e_sender.get().strip(); r = e_receiver.get().strip()
        if not s or not r: messagebox.showerror("Error","Enter sender and receiver IDs"); return
        txt = entry.get().strip(); img = img_var.get() or None
        if not txt and not img: messagebox.showwarning("Empty","Type message or attach image"); return
        send_message(s, r, txt, img)
        entry.delete(0,tk.END); img_var.set(""); refresh()
    def refresh():
        box.delete(0,tk.END)
        s = e_sender.get().strip(); r = e_receiver.get().strip()
        if not s or not r: return
        for m in get_conversation(s, r):
            ts = m.get('ts') or m.get('timestamp') or ''
            who = "You" if str(m.get('sender'))==str(s) else f"User {m.get('sender')}"
            line = f"[{ts}] {who}: {m.get('text')}"
            if m.get('img'): line += f" [Image:{m.get('img')}]"
            box.insert(tk.END, line)
        box.yview_moveto(1.0)
    tk.Button(bottom,text="Attach",command=browse).pack(side="left",padx=4)
    tk.Button(bottom,text="Send",command=do_send).pack(side="left",padx=4)
    tk.Button(top,text="Load convo",command=refresh).grid(row=0,column=4,padx=6)

# Search Window
def search_window(parent):
    win = tk.Toplevel(parent); win.title("Search"); win.geometry("880x520")
    frm = tk.Frame(win); frm.pack(padx=10, pady=8)

    tk.Label(frm, text="Appointment ID").grid(row=0, column=0, sticky="e")
    e_appt = tk.Entry(frm, width=20); e_appt.grid(row=0, column=1, padx=6, pady=4)

    tk.Label(frm, text="Patient ID").grid(row=0, column=2, sticky="e")
    e_patient = tk.Entry(frm, width=20); e_patient.grid(row=0, column=3, padx=6, pady=4)

    tk.Label(frm, text="Doctor name (partial)").grid(row=1, column=0, sticky="e")
    e_doctor = tk.Entry(frm, width=30); e_doctor.grid(row=1, column=1, padx=6, pady=4)

    tk.Label(frm, text="Date From (YYYY-MM-DD)").grid(row=1, column=2, sticky="e")
    e_from = tk.Entry(frm, width=20); e_from.grid(row=1, column=3, padx=6, pady=4)

    tk.Label(frm, text="Date To (YYYY-MM-DD)").grid(row=2, column=2, sticky="e")
    e_to = tk.Entry(frm, width=20); e_to.grid(row=2, column=3, padx=6, pady=4)

    result_box = tk.Listbox(win, width=130, height=22)
    result_box.pack(padx=10, pady=(6,12), fill="both", expand=True)

    def parse_date(s):
        s = s.strip()
        if not s:
            return None
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except:
            return None

    def do_search():
        result_box.delete(0, tk.END)
        appt_val = e_appt.get().strip()
        pid_val = e_patient.get().strip()
        doc_val = e_doctor.get().strip()
        dfrom = parse_date(e_from.get())
        dto = parse_date(e_to.get())

        # 1) Appointment ID exact
        if appt_val:
            try:
                aid = int(appt_val)
            except:
                messagebox.showerror("Input", "Appointment ID must be an integer"); return
            cy = """
            MATCH (a:Appointment {appt_id:$aid})
            OPTIONAL MATCH (d:Doctor)-[:HAS_APPOINTMENT]->(a)
            OPTIONAL MATCH (p:Patient)-[:HAS_APPOINTMENT]->(a)
            RETURN a.appt_id AS id, a.date AS date, a.time AS time, d.name AS doctor, p.name AS patient
            """
            rows = run_query(cy, {"aid": aid})
            if not rows:
                result_box.insert(tk.END, f"No appointment with ID {aid}")
            else:
                for r in rows:
                    result_box.insert(tk.END, f"#{r['id']} | {r['date']} {r['time']} | Dr:{r.get('doctor')} with {r.get('patient')}")
            return

        # 2) Patient ID exact -> list appointments for that patient
        if pid_val:
            try:
                pid = int(pid_val)
            except:
                messagebox.showerror("Input", "Patient ID must be an integer"); return
            cy = """
            MATCH (p:Patient {patient_id:$pid})-[:HAS_APPOINTMENT]->(a:Appointment)
            OPTIONAL MATCH (d:Doctor)-[:HAS_APPOINTMENT]->(a)
            RETURN a.appt_id AS id, a.date AS date, a.time AS time, d.name AS doctor
            ORDER BY a.date, a.time
            """
            rows = run_query(cy, {"pid": pid})
            if not rows:
                result_box.insert(tk.END, f"No appointments for patient {pid}")
            else:
                result_box.insert(tk.END, f"Appointments for patient {pid}:")
                for r in rows:
                    # date filter
                    if dfrom or dto:
                        try:
                            ad = datetime.strptime(r['date'], "%Y-%m-%d").date()
                        except:
                            ad = None
                        if dfrom and ad and ad < dfrom: continue
                        if dto and ad and ad > dto: continue
                    result_box.insert(tk.END, f"  Appt #{r['id']} | {r['date']} {r['time']} | Dr:{r.get('doctor')}")
            return

        # 3) Doctor name partial -> show matching doctors and their appointments
        if doc_val:
            pattern = doc_val.strip().lower()
            cy = "MATCH (d:Doctor) WHERE toLower(d.name) CONTAINS $pat RETURN d.doctor_id AS id, d.name AS name"
            docs = run_query(cy, {"pat": pattern})
            if not docs:
                result_box.insert(tk.END, f"No doctors match '{doc_val}'")
                return
            for d in docs:
                result_box.insert(tk.END, f"Doctor #{d['id']} | {d['name']}")
                # appointments for this doctor
                cy2 = """
                MATCH (d:Doctor {doctor_id:$did})-[:HAS_APPOINTMENT]->(a:Appointment)<-[:HAS_APPOINTMENT]-(p:Patient)
                RETURN a.appt_id AS id, a.date AS date, a.time AS time, p.patient_id AS pid, p.name AS pname
                ORDER BY a.date, a.time
                """
                rows = run_query(cy2, {"did": int(d["id"])})
                for r in rows:
                    if dfrom or dto:
                        try:
                            ad = datetime.strptime(r['date'], "%Y-%m-%d").date()
                        except:
                            ad = None
                        if dfrom and ad and ad < dfrom: continue
                        if dto and ad and ad > dto: continue
                    result_box.insert(tk.END, f"  Appt #{r['id']} | {r['date']} {r['time']} | Patient #{r['pid']} {r['pname']}")
            return

        # 4) Date range only -> list all appointments in range
        if dfrom or dto:
            cy = """
            MATCH (d:Doctor)-[:HAS_APPOINTMENT]->(a:Appointment)<-[:HAS_APPOINTMENT]-(p:Patient)
            RETURN a.appt_id AS id, a.date AS date, a.time AS time, d.name AS doctor, p.name AS patient
            ORDER BY a.date, a.time
            """
            rows = run_query(cy)
            found = False
            for r in rows:
                try:
                    ad = datetime.strptime(r['date'], "%Y-%m-%d").date()
                except:
                    ad = None
                if ad:
                    if dfrom and ad < dfrom: continue
                    if dto and ad > dto: continue
                    result_box.insert(tk.END, f"#{r['id']} | {r['date']} {r['time']} | Dr:{r['doctor']} with {r['patient']}")
                    found = True
            if not found:
                result_box.insert(tk.END, "No appointments in the given date range")
            return

        # 5) nothing provided
        result_box.insert(tk.END, "Enter Appointment ID, Patient ID, Doctor name, or a Date range and press Search.")

    btns = tk.Frame(win); btns.pack(pady=6)
    tk.Button(btns, text="Search", command=do_search).pack(side="left", padx=6)
    tk.Button(btns, text="Clear", command=lambda: result_box.delete(0, tk.END)).pack(side="left", padx=6)
