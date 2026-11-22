from django.test import TestCase, Client
from django.utils import timezone
from accounts.models import CustomUser
from doctors.models import Department, DoctorProfile
from patients.models import PatientProfile
from queue_management.models import QueueToken, Consultation
from queue_management.services import (
    generate_queue_token,
    call_next_patient,
    start_consultation,
    complete_consultation,
    assign_emergency_priority,
    get_doctor_queue,
)
import datetime


class QueueManagementTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Cardiology', code='CARD')

        self.doc_user = CustomUser.objects.create_user(
            username='dr.test',
            password='password123',
            role=CustomUser.Role.DOCTOR,
            first_name='Test',
            last_name='Doctor'
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            specialization='Cardiology',
            qualification='MD',
            room_number='Room 101',
            avg_consultation_time=15,
            daily_capacity=30
        )

        self.pat_user1 = CustomUser.objects.create_user(
            username='pat1',
            password='password123',
            role=CustomUser.Role.PATIENT,
            first_name='Patient',
            last_name='One'
        )
        PatientProfile.objects.create(user=self.pat_user1, blood_group='A+')

        self.pat_user2 = CustomUser.objects.create_user(
            username='pat2',
            password='password123',
            role=CustomUser.Role.PATIENT,
            first_name='Patient',
            last_name='Two'
        )
        PatientProfile.objects.create(user=self.pat_user2, blood_group='B+')

        self.pat_user3 = CustomUser.objects.create_user(
            username='pat3',
            password='password123',
            role=CustomUser.Role.PATIENT,
            first_name='Patient',
            last_name='Three'
        )
        PatientProfile.objects.create(user=self.pat_user3, blood_group='O+')

    def test_token_generation_sequence(self):
        """Test daily sequential token generation for a doctor."""
        t1 = generate_queue_token(self.doctor, self.pat_user1)
        t2 = generate_queue_token(self.doctor, self.pat_user2)

        self.assertEqual(t1.token_sequence, 1)
        self.assertEqual(t1.token_number, 'CARD-001')
        self.assertEqual(t2.token_sequence, 2)
        self.assertEqual(t2.token_number, 'CARD-002')

    def test_emergency_priority_reordering(self):
        """Test that emergency priority elevates patient ahead of normal FIFO queue."""
        t1 = generate_queue_token(self.doctor, self.pat_user1, priority=QueueToken.Priority.NORMAL)
        t2 = generate_queue_token(self.doctor, self.pat_user2, priority=QueueToken.Priority.NORMAL)
        # pat3 arrives later with Emergency Priority
        t3 = generate_queue_token(self.doctor, self.pat_user3, priority=QueueToken.Priority.EMERGENCY, priority_notes="Severe pain")

        # When doctor calls next patient, t3 (Emergency) should be called first!
        called = call_next_patient(self.doctor)
        self.assertEqual(called.id, t3.id)
        self.assertEqual(called.status, QueueToken.Status.CALLED)

    def test_wait_time_calculation(self):
        """Test waiting time estimation calculation."""
        t1 = generate_queue_token(self.doctor, self.pat_user1)
        t2 = generate_queue_token(self.doctor, self.pat_user2)

        pos1, wait1 = t1.calculate_position_and_wait_time()
        pos2, wait2 = t2.calculate_position_and_wait_time()

        self.assertEqual(pos1, 1)
        self.assertEqual(wait1, 0)
        self.assertEqual(pos2, 2)
        self.assertEqual(wait2, 15)  # 1 patient ahead * 15 mins avg

    def test_consultation_completion(self):
        """Test full consultation workflow."""
        token = generate_queue_token(self.doctor, self.pat_user1)
        start_consultation(token)
        self.assertEqual(token.status, QueueToken.Status.IN_CONSULTATION)

        consultation = complete_consultation(
            token=token,
            symptoms='Headache',
            diagnosis='Tension Headache',
            prescription='Paracetamol 500mg'
        )

        self.assertEqual(token.status, QueueToken.Status.COMPLETED)
        self.assertEqual(consultation.diagnosis, 'Tension Headache')
        self.assertTrue(Consultation.objects.filter(token=token).exists())
