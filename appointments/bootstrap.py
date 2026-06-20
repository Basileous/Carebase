import logging
from datetime import time

from django.contrib.sites.models import Site
from django.core.management import call_command
from django.db import OperationalError, ProgrammingError, transaction

from .models import Doctor, DoctorTimeSlot

logger = logging.getLogger(__name__)

DEFAULT_DOCTORS = [
    ("Ahmed Jan", "General Medicine"),
    ("Zoya Hassan", "Cardiology"),
    ("Sara Malik", "Pediatrics"),
    ("Bilal Raza", "Neurology"),
    ("Omar Farooq", "Dermatology"),
]

DEFAULT_SLOTS = [
    ("Monday", time(9, 0)),
    ("Monday", time(11, 0)),
    ("Tuesday", time(10, 0)),
    ("Wednesday", time(14, 0)),
    ("Thursday", time(12, 0)),
    ("Friday", time(15, 0)),
]

_bootstrap_done = False


def bootstrap_deployment(site_domain="carebase.vercel.app"):
    """Prepare a fresh serverless database for login and booking.

    Safe to call repeatedly — uses a module-level guard to run only once
    per process and wraps all work in try/except so a failure never
    crashes the WSGI entry-point.
    """
    global _bootstrap_done
    if _bootstrap_done:
        return
    _bootstrap_done = True

    try:
        logger.info("Running migrations …")
        call_command("migrate", interactive=False, verbosity=0)
    except Exception as exc:
        logger.warning("migrate failed: %s", exc)
        return  # tables don't exist yet — nothing else to do

    try:
        with transaction.atomic():
            Site.objects.update_or_create(
                id=1,
                defaults={"domain": site_domain, "name": "CareBase"},
            )

            for name, specialty in DEFAULT_DOCTORS:
                doctor, _ = Doctor.objects.get_or_create(
                    name=name,
                    defaults={"specialty": specialty},
                )
                if doctor.specialty != specialty:
                    doctor.specialty = specialty
                    doctor.save(update_fields=["specialty"])

                for day, slot_time in DEFAULT_SLOTS:
                    DoctorTimeSlot.objects.get_or_create(
                        doctor=doctor,
                        day=day,
                        time_slot=slot_time,
                    )
        logger.info("Bootstrap complete — %d doctors seeded.", len(DEFAULT_DOCTORS))
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("Bootstrap seeding failed (tables may not exist): %s", exc)
    except Exception as exc:
        logger.warning("Bootstrap unexpected error: %s", exc)
