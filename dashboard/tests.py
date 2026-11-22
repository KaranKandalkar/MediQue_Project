from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from doctors.models import Department, DoctorProfile
from patients.models import PatientProfile


class DashboardViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Cardiology', code='CARD')

        self.admin = CustomUser.objects.create_superuser(
            username='admin_test',
            password='password123',
            role=CustomUser.Role.ADMIN
        )

        self.doc_user = CustomUser.objects.create_user(
            username='doctor_test',
            password='password123',
            role=CustomUser.Role.DOCTOR,
            first_name='Dr',
            last_name='Doc'
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            room_number='101'
        )

        self.receptionist = CustomUser.objects.create_user(
            username='rec_test',
            password='password123',
            role=CustomUser.Role.RECEPTIONIST
        )

        self.patient_user = CustomUser.objects.create_user(
            username='pat_test',
            password='password123',
            role=CustomUser.Role.PATIENT,
            first_name='Pat',
            last_name='Ient'
        )
        self.patient_profile = PatientProfile.objects.create(user=self.patient_user)

    def test_public_pages(self):
        """Home and public display board render 200 without login."""
        res_home = self.client.get(reverse('home'))
        self.assertEqual(res_home.status_code, 200)

        res_board = self.client.get(reverse('queue_management:public_display_board'))
        self.assertEqual(res_board.status_code, 200)

    def test_admin_dashboard(self):
        self.client.login(username='admin_test', password='password123')
        res = self.client.get(reverse('dashboard:admin'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Hospital Administration & Analytics')

    def test_doctor_dashboard(self):
        self.client.login(username='doctor_test', password='password123')
        res = self.client.get(reverse('dashboard:doctor'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Doctor Clinical Desk')

    def test_receptionist_dashboard(self):
        self.client.login(username='rec_test', password='password123')
        res = self.client.get(reverse('dashboard:receptionist'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Reception & Front Desk Management')

    def test_patient_dashboard(self):
        self.client.login(username='pat_test', password='password123')
        res = self.client.get(reverse('dashboard:patient'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Patient Portal')
