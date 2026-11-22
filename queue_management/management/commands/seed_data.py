import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CustomUser
from doctors.models import Department, DoctorProfile
from patients.models import PatientProfile
from hospital_resources.models import HospitalResource
from appointments.models import Appointment
from queue_management.models import QueueToken, Consultation, Notification


class Command(BaseCommand):
    help = 'Seeds MediQueue database with realistic demonstration data for all roles and workflows'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding MediQueue database..."))
        today = timezone.localdate()

        # 1. Create Superuser / Admin
        admin_user, _ = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@mediqueue.health',
                'first_name': 'Chief',
                'last_name': 'Administrator',
                'role': CustomUser.Role.ADMIN,
                'phone_number': '+1-800-555-0100',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()
        self.stdout.write(self.style.SUCCESS("  [+] Admin user created: admin / admin123"))

        # 2. Create Receptionist
        receptionist_user, _ = CustomUser.objects.get_or_create(
            username='receptionist',
            defaults={
                'email': 'reception@mediqueue.health',
                'first_name': 'Clara',
                'last_name': 'Oswald',
                'role': CustomUser.Role.RECEPTIONIST,
                'phone_number': '+1-800-555-0101',
                'is_staff': False,
            }
        )
        receptionist_user.set_password('reception123')
        receptionist_user.save()
        self.stdout.write(self.style.SUCCESS("  [+] Receptionist user created: receptionist / reception123"))

        # 3. Create 5 Hospital Departments
        depts_data = [
            ('Cardiology', 'CARD', 'Comprehensive cardiac care, interventional cardiology, and heart rhythm management.', 'bi-heart-pulse'),
            ('Pediatrics', 'PEDI', 'Specialized care for infants, children, and adolescents.', 'bi-emoji-smile'),
            ('Orthopedics', 'ORTH', 'Bone, joint, musculoskeletal trauma, and sports medicine.', 'bi-bandaid'),
            ('General Medicine', 'GEN', 'Primary care, adult preventative health, and systemic diagnostics.', 'bi-hospital'),
            ('Dermatology', 'DERM', 'Clinical skin diagnostics, allergy testing, and cosmetic care.', 'bi-shield-plus'),
        ]

        departments = {}
        for name, code, desc, icon in depts_data:
            dept, _ = Department.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': desc,
                    'icon': icon,
                    'is_active': True,
                }
            )
            departments[code] = dept
        self.stdout.write(self.style.SUCCESS(f"  [+] 5 Departments created."))

        # 4. Create 8 Doctors with DoctorProfile
        doctors_data = [
            ('dr.smith', 'doctor123', 'Alexander', 'Smith', 'CARD', 'Interventional Cardiologist', 'MBBS, MD (Cardiology), FACC', 80.00, 'Room 101', 15, 30),
            ('dr.johnson', 'doctor123', 'Emily', 'Johnson', 'PEDI', 'Pediatric Specialist', 'MBBS, DCH, MD (Pediatrics)', 60.00, 'Room 102', 12, 35),
            ('dr.patel', 'doctor123', 'Rajesh', 'Patel', 'ORTH', 'Orthopedic Surgeon', 'MBBS, MS (Ortho), FRCS', 90.00, 'Room 103', 20, 25),
            ('dr.chen', 'doctor123', 'Wei', 'Chen', 'GEN', 'Internal Medicine Consultant', 'MD, FACP', 50.00, 'Room 104', 15, 40),
            ('dr.garcia', 'doctor123', 'Sofia', 'Garcia', 'DERM', 'Dermatologist & Allergist', 'MBBS, DVD, MD (Dermatology)', 70.00, 'Room 105', 15, 30),
            ('dr.davis', 'doctor123', 'Marcus', 'Davis', 'CARD', 'Cardiac Electrophysiologist', 'MBBS, MD, FHRS', 85.00, 'Room 106', 15, 25),
            ('dr.wilson', 'doctor123', 'Sarah', 'Wilson', 'PEDI', 'Neonatal & Child Health', 'MBBS, MRCPCH', 65.00, 'Room 107', 15, 30),
            ('dr.taylor', 'doctor123', 'James', 'Taylor', 'GEN', 'Family Medicine Physician', 'MBBS, MRCGP', 50.00, 'Room 108', 12, 40),
        ]

        doctors_list = []
        for uname, pwd, fname, lname, dept_code, spec, qual, fee, room, avg_time, cap in doctors_data:
            doc_user, _ = CustomUser.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f"{uname}@mediqueue.health",
                    'first_name': fname,
                    'last_name': lname,
                    'role': CustomUser.Role.DOCTOR,
                    'phone_number': f"+1-555-01{len(doctors_list)+10}",
                }
            )
            doc_user.set_password(pwd)
            doc_user.save()

            doc_profile, _ = DoctorProfile.objects.get_or_create(
                user=doc_user,
                defaults={
                    'department': departments[dept_code],
                    'specialization': spec,
                    'qualification': qual,
                    'consultation_fee': fee,
                    'room_number': room,
                    'avg_consultation_time': avg_time,
                    'daily_capacity': cap,
                    'is_available': True,
                    'available_days': 'Monday,Tuesday,Wednesday,Thursday,Friday',
                    'shift_start': datetime.time(9, 0),
                    'shift_end': datetime.time(17, 0),
                }
            )
            doctors_list.append(doc_profile)
        self.stdout.write(self.style.SUCCESS(f"  [+] 8 Doctors created with profiles and credentials."))

        # 5. Create Hospital Rooms & Resources
        rooms_data = [
            ('Room 101', 'Room 101 - Cardiology Suite', HospitalResource.ResourceType.CONSULTATION_ROOM, departments['CARD'], doctors_list[0], HospitalResource.Status.AVAILABLE),
            ('Room 102', 'Room 102 - Pediatrics Clinic', HospitalResource.ResourceType.CONSULTATION_ROOM, departments['PEDI'], doctors_list[1], HospitalResource.Status.AVAILABLE),
            ('Room 103', 'Room 103 - Orthopedic Suite', HospitalResource.ResourceType.CONSULTATION_ROOM, departments['ORTH'], doctors_list[2], HospitalResource.Status.AVAILABLE),
            ('Room 104', 'Room 104 - Internal Medicine', HospitalResource.ResourceType.CONSULTATION_ROOM, departments['GEN'], doctors_list[3], HospitalResource.Status.AVAILABLE),
            ('Room 105', 'Room 105 - Dermatology Room', HospitalResource.ResourceType.CONSULTATION_ROOM, departments['DERM'], doctors_list[4], HospitalResource.Status.AVAILABLE),
            ('Room 106', 'Room 106 - Cardiac Lab Room', HospitalResource.ResourceType.CONSULTATION_ROOM, departments['CARD'], doctors_list[5], HospitalResource.Status.AVAILABLE),
            ('Room 107', 'Room 107 - Child Wellness Wing', HospitalResource.ResourceType.CONSULTATION_ROOM, departments['PEDI'], doctors_list[6], HospitalResource.Status.AVAILABLE),
            ('Room 108', 'Room 108 - Family Care Cabin', HospitalResource.ResourceType.CONSULTATION_ROOM, departments['GEN'], doctors_list[7], HospitalResource.Status.AVAILABLE),
            ('ICU-01', 'Intensive Care Bay 1', HospitalResource.ResourceType.ICU_BED, departments['CARD'], None, HospitalResource.Status.OCCUPIED),
            ('ICU-02', 'Intensive Care Bay 2', HospitalResource.ResourceType.ICU_BED, departments['CARD'], None, HospitalResource.Status.AVAILABLE),
            ('ER-Bay-1', 'Emergency Triage Bay 1', HospitalResource.ResourceType.EMERGENCY_BAY, departments['GEN'], None, HospitalResource.Status.OCCUPIED),
            ('ER-Bay-2', 'Emergency Triage Bay 2', HospitalResource.ResourceType.EMERGENCY_BAY, departments['GEN'], None, HospitalResource.Status.AVAILABLE),
        ]

        for r_num, name, r_type, dept, doc, status in rooms_data:
            HospitalResource.objects.update_or_create(
                room_number=r_num,
                defaults={
                    'name': name,
                    'resource_type': r_type,
                    'department': dept,
                    'assigned_doctor': doc,
                    'status': status,
                    'capacity': 1,
                    'notes': 'Equipped with digital monitoring and diagnostic instruments.',
                }
            )
        self.stdout.write(self.style.SUCCESS("  [+] 12 Hospital Resources (Rooms, ICU, ER Bays) created."))

        # 6. Create 20 Sample Patients
        patients_raw = [
            ('patient1', 'patient123', 'John', 'Doe', 'M', '1988-04-12', 'O+', 'Penicillin', 'Mild hypertension'),
            ('patient2', 'patient234', 'Jane', 'Roe', 'F', '1992-09-23', 'A+', 'None', 'Asthma'),
            ('patient3', 'patient123', 'Robert', 'Miller', 'M', '1975-01-15', 'B+', 'Aspirin', 'Type 2 Diabetes'),
            ('patient4', 'patient123', 'Alice', 'Walker', 'F', '2001-11-05', 'AB+', 'Sulfa drugs', 'None'),
            ('patient5', 'patient123', 'David', 'Clark', 'M', '1963-06-30', 'O-', 'Ibuprofen', 'Coronary artery disease'),
            ('patient6', 'patient123', 'Maria', 'Hernandez', 'F', '1985-08-18', 'A-', 'None', 'Migraine'),
            ('patient7', 'patient123', 'Michael', 'Brown', 'M', '2016-03-22', 'B-', 'Peanuts', 'Childhood asthma'),
            ('patient8', 'patient123', 'Emma', 'Taylor', 'F', '2018-07-11', 'O+', 'None', 'None'),
            ('patient9', 'patient123', 'William', 'Anderson', 'M', '1955-12-04', 'AB-', 'Codeine', 'Osteoarthritis, Knee replacement'),
            ('patient10', 'patient123', 'Olivia', 'Thomas', 'F', '1995-02-14', 'A+', 'Latex', 'Eczema'),
            ('patient11', 'patient123', 'James', 'Jackson', 'M', '1982-10-29', 'B+', 'None', 'None'),
            ('patient12', 'patient123', 'Sophia', 'White', 'F', '1990-05-19', 'O+', 'Ciprofloxacin', 'GERD'),
            ('patient13', 'patient123', 'Daniel', 'Harris', 'M', '1978-08-08', 'A-', 'None', 'Lumbar disc herniation'),
            ('patient14', 'patient123', 'Isabella', 'Martin', 'F', '2020-09-01', 'O+', 'Egg protein', 'Recurrent bronchitis'),
            ('patient15', 'patient123', 'Lucas', 'Thompson', 'M', '1999-12-12', 'AB+', 'None', 'Sports ACL injury'),
            ('patient16', 'patient123', 'Mia', 'Garcia', 'F', '1987-03-27', 'B-', 'None', 'Thyroid disorder'),
            ('patient17', 'patient123', 'Benjamin', 'Martinez', 'M', '1970-11-17', 'O+', 'None', 'Hypertension'),
            ('patient18', 'patient123', 'Charlotte', 'Robinson', 'F', '1994-07-04', 'A+', 'Amoxicillin', 'Psoriasis'),
            ('patient19', 'patient123', 'Henry', 'Lee', 'M', '1968-09-15', 'B+', 'None', 'Hyperlipidemia'),
            ('patient20', 'patient123', 'Amelia', 'Scott', 'F', '2005-01-20', 'O-', 'None', 'Allergic rhinitis'),
        ]

        patients_list = []
        for uname, pwd, fname, lname, gender, dob, bg, allergies, history in patients_raw:
            p_user, _ = CustomUser.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f"{uname}@example.com",
                    'first_name': fname,
                    'last_name': lname,
                    'role': CustomUser.Role.PATIENT,
                    'phone_number': f"+1-555-02{len(patients_list)+10}",
                }
            )
            p_user.set_password(pwd)
            p_user.save()

            p_profile, _ = PatientProfile.objects.get_or_create(
                user=p_user,
                defaults={
                    'date_of_birth': datetime.date.fromisoformat(dob),
                    'gender': gender,
                    'blood_group': bg,
                    'emergency_contact': f"+1-555-99{len(patients_list)+10}",
                    'address': f"{100 + len(patients_list)} Healthway Ave, Metro City",
                    'allergies': allergies,
                    'medical_history': history,
                }
            )
            patients_list.append(p_user)
        self.stdout.write(self.style.SUCCESS(f"  [+] 20 Sample Patients created with full medical records."))

        # 7. Create Appointments for Today and Upcoming
        dr_smith = doctors_list[0]
        dr_johnson = doctors_list[1]
        dr_patel = doctors_list[2]

        appts = [
            (patients_list[0], dr_smith, today, datetime.time(9, 0), Appointment.Status.COMPLETED, "Routine cardiac follow-up"),
            (patients_list[1], dr_smith, today, datetime.time(9, 30), Appointment.Status.CHECKED_IN, "Mild chest flutter after exertion"),
            (patients_list[2], dr_smith, today, datetime.time(10, 0), Appointment.Status.SCHEDULED, "Blood pressure check and ECG review"),
            (patients_list[3], dr_smith, today, datetime.time(10, 30), Appointment.Status.SCHEDULED, "Palpitations during exercise"),
            (patients_list[6], dr_johnson, today, datetime.time(9, 15), Appointment.Status.COMPLETED, "Seasonal cough and mild fever"),
            (patients_list[7], dr_johnson, today, datetime.time(9, 45), Appointment.Status.CHECKED_IN, "Wellness immunizations and checkup"),
            (patients_list[8], dr_patel, today, datetime.time(10, 0), Appointment.Status.SCHEDULED, "Right knee arthritic stiffness"),
            (patients_list[9], doctors_list[4], today, datetime.time(11, 0), Appointment.Status.SCHEDULED, "Persistent skin rash on forearms"),
            # Upcoming
            (patients_list[4], dr_smith, today + datetime.timedelta(days=1), datetime.time(9, 30), Appointment.Status.SCHEDULED, "Post-stent 6 month evaluation"),
            (patients_list[5], dr_johnson, today + datetime.timedelta(days=2), datetime.time(10, 0), Appointment.Status.SCHEDULED, "Allergy panel discussion"),
        ]

        created_appts = []
        for pat, doc, a_date, a_time, status, reason in appts:
            appt, _ = Appointment.objects.update_or_create(
                doctor=doc,
                appointment_date=a_date,
                appointment_time=a_time,
                defaults={
                    'patient': pat,
                    'department': doc.department,
                    'status': status,
                    'reason': reason,
                }
            )
            created_appts.append(appt)
        self.stdout.write(self.style.SUCCESS("  [+] Appointments scheduled."))

        # 8. Create Queue Tokens and Consultations for Today
        # Dr. Smith's Queue Tokens
        t1, _ = QueueToken.objects.update_or_create(
            doctor=dr_smith,
            token_date=today,
            token_sequence=1,
            defaults={
                'token_number': 'CARD-001',
                'patient': patients_list[0],
                'department': dr_smith.department,
                'appointment': created_appts[0],
                'priority': QueueToken.Priority.NORMAL,
                'status': QueueToken.Status.COMPLETED,
                'called_at': timezone.now() - datetime.timedelta(minutes=45),
                'consultation_started_at': timezone.now() - datetime.timedelta(minutes=40),
                'completed_at': timezone.now() - datetime.timedelta(minutes=25),
            }
        )

        Consultation.objects.update_or_create(
            token=t1,
            defaults={
                'doctor': dr_smith,
                'patient': patients_list[0],
                'start_time': t1.consultation_started_at,
                'end_time': t1.completed_at,
                'duration_minutes': 15,
                'symptoms': 'Routine hypertension follow-up. Mild fatigue reported.',
                'diagnosis': 'Stage 1 Essential Hypertension (Well Controlled)',
                'prescription': "1. Tab. Amlodipine 5mg - 1 tablet once daily in the morning.\n2. Tab. Aspirin 75mg - 1 tablet daily after lunch.\n3. Lifestyle: Low sodium DASH diet & 30 min daily brisk walk.",
                'vital_signs': {'bp': '124/82 mmHg', 'pulse': '72 bpm', 'temperature': '98.4 F', 'spo2': '99%'},
                'follow_up_date': today + datetime.timedelta(days=60),
                'notes': 'Lipid profile and serum electrolytes ordered for next visit.',
            }
        )

        t2, _ = QueueToken.objects.update_or_create(
            doctor=dr_smith,
            token_date=today,
            token_sequence=2,
            defaults={
                'token_number': 'CARD-002',
                'patient': patients_list[1],
                'department': dr_smith.department,
                'appointment': created_appts[1],
                'priority': QueueToken.Priority.NORMAL,
                'status': QueueToken.Status.IN_CONSULTATION,
                'called_at': timezone.now() - datetime.timedelta(minutes=10),
                'consultation_started_at': timezone.now() - datetime.timedelta(minutes=8),
            }
        )

        # Emergency Priority Token (t3)
        t3, _ = QueueToken.objects.update_or_create(
            doctor=dr_smith,
            token_date=today,
            token_sequence=3,
            defaults={
                'token_number': 'CARD-003',
                'patient': patients_list[4],
                'department': dr_smith.department,
                'priority': QueueToken.Priority.EMERGENCY,
                'priority_assigned_by': receptionist_user,
                'priority_notes': 'Acute retrosternal discomfort radiating to left shoulder. Stat triage.',
                'status': QueueToken.Status.WAITING,
                'estimated_wait_time': 5,
            }
        )

        t4, _ = QueueToken.objects.update_or_create(
            doctor=dr_smith,
            token_date=today,
            token_sequence=4,
            defaults={
                'token_number': 'CARD-004',
                'patient': patients_list[2],
                'department': dr_smith.department,
                'appointment': created_appts[2],
                'priority': QueueToken.Priority.NORMAL,
                'status': QueueToken.Status.WAITING,
                'estimated_wait_time': 20,
            }
        )

        t5, _ = QueueToken.objects.update_or_create(
            doctor=dr_smith,
            token_date=today,
            token_sequence=5,
            defaults={
                'token_number': 'CARD-005',
                'patient': patients_list[3],
                'department': dr_smith.department,
                'appointment': created_appts[3],
                'priority': QueueToken.Priority.NORMAL,
                'status': QueueToken.Status.WAITING,
                'estimated_wait_time': 35,
            }
        )

        # Dr. Johnson (Pediatrics) Tokens
        p1, _ = QueueToken.objects.update_or_create(
            doctor=dr_johnson,
            token_date=today,
            token_sequence=1,
            defaults={
                'token_number': 'PEDI-001',
                'patient': patients_list[6],
                'department': dr_johnson.department,
                'appointment': created_appts[4],
                'priority': QueueToken.Priority.NORMAL,
                'status': QueueToken.Status.COMPLETED,
                'called_at': timezone.now() - datetime.timedelta(minutes=50),
                'consultation_started_at': timezone.now() - datetime.timedelta(minutes=45),
                'completed_at': timezone.now() - datetime.timedelta(minutes=30),
            }
        )

        Consultation.objects.update_or_create(
            token=p1,
            defaults={
                'doctor': dr_johnson,
                'patient': patients_list[6],
                'start_time': p1.consultation_started_at,
                'end_time': p1.completed_at,
                'duration_minutes': 15,
                'symptoms': 'Upper respiratory congestion, rhinitis, low-grade fever for 2 days.',
                'diagnosis': 'Acute Viral Nasopharyngitis (Common Cold)',
                'prescription': "1. Syp. Paracetamol (120mg/5ml) - 5ml SOS for fever > 100 F.\n2. Saline nasal drops - 2 drops per nostril before sleep.\n3. Steam inhalation and warm fluids.",
                'vital_signs': {'bp': '95/60 mmHg', 'pulse': '92 bpm', 'temperature': '99.2 F', 'spo2': '99%'},
                'follow_up_date': today + datetime.timedelta(days=5),
                'notes': 'Advised parents to return if breathing difficulty or high persistent fever occurs.',
            }
        )

        p2, _ = QueueToken.objects.update_or_create(
            doctor=dr_johnson,
            token_date=today,
            token_sequence=2,
            defaults={
                'token_number': 'PEDI-002',
                'patient': patients_list[7],
                'department': dr_johnson.department,
                'appointment': created_appts[5],
                'priority': QueueToken.Priority.NORMAL,
                'status': QueueToken.Status.WAITING,
                'estimated_wait_time': 10,
            }
        )

        self.stdout.write(self.style.SUCCESS("  [+] Queue tokens and clinical consultations seeded."))

        # 9. Create Welcome System Notifications
        Notification.objects.get_or_create(
            user=patients_list[0],
            title="Prescription Available",
            defaults={'message': "Your consultation summary with Dr. Alexander Smith has been posted.", 'notification_type': 'QUEUE'}
        )
        Notification.objects.get_or_create(
            user=patients_list[4],
            title="Urgent Triage Attention",
            defaults={'message': "Token CARD-003 has been prioritized as Emergency. Please wait near Room 101.", 'notification_type': 'EMERGENCY'}
        )

        self.stdout.write(self.style.SUCCESS("\nMediQueue database successfully seeded with all demonstration data!"))
        self.stdout.write(self.style.NOTICE("Standard Credentials:"))
        self.stdout.write("  - Administrator: admin / admin123")
        self.stdout.write("  - Specialist Doctor: dr.smith / doctor123")
        self.stdout.write("  - Pediatric Specialist: dr.johnson / doctor123")
        self.stdout.write("  - Front Receptionist: receptionist / reception123")
        self.stdout.write("  - Patient (John Doe): patient1 / patient123")
        self.stdout.write("  - Patient (Jane Roe): patient2 / patient234\n")
