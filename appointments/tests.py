from django.test import TestCase
from django.utils import timezone
from accounts.models import CustomUser
from doctors.models import Department, DoctorProfile
from appointments.models import Appointment
from appointments.forms import AppointmentBookingForm
import datetime


class AppointmentTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='Pediatrics', code='PEDI')

        self.doc_user = CustomUser.objects.create_user(
            username='dr.pedi',
            password='password123',
            role=CustomUser.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            specialization='Pediatrics',
            daily_capacity=2
        )

        self.patient = CustomUser.objects.create_user(
            username='pat.test',
            password='password123',
            role=CustomUser.Role.PATIENT
        )

    def test_duplicate_slot_validation(self):
        """Test appointment booking form prevents double booking the same slot."""
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        slot_time = datetime.time(10, 0)

        # Existing appointment
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            department=self.dept,
            appointment_date=tomorrow,
            appointment_time=slot_time,
            reason='First checkup'
        )

        # Attempt to book another appointment at the exact same slot
        form = AppointmentBookingForm(data={
            'department': self.dept.id,
            'doctor': self.doctor.id,
            'appointment_date': tomorrow,
            'appointment_time': slot_time,
            'reason': 'Second checkup attempt'
        })

        self.assertFalse(form.is_valid())
        self.assertIn('appointment_time', form.errors)
