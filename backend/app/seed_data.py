"""
Seeds a few sample HCPs and materials on first run, so the app has data to
show immediately — no manual SQL required when using the default SQLite
database.
"""
from app.database import SessionLocal
from app.models import HCP, Material


def seed_if_empty():
    db = SessionLocal()
    try:
        if db.query(HCP).count() > 0:
            return  # already seeded

        db.add_all([
            HCP(name="Dr. Aditi Sharma", specialty="Cardiology",
                hospital="Manipal Hospital, Bengaluru", email="aditi.sharma@example.com",
                phone="+91-9876500001", tier="A"),
            HCP(name="Dr. Rohan Mehta", specialty="Endocrinology",
                hospital="Apollo Hospitals, Chennai", email="rohan.mehta@example.com",
                phone="+91-9876500002", tier="B"),
            HCP(name="Dr. Neha Kapoor", specialty="Oncology",
                hospital="Fortis Hospital, Delhi", email="neha.kapoor@example.com",
                phone="+91-9876500003", tier="A"),
        ])
        db.add_all([
            Material(name="CardioPlus Efficacy Brochure", type="brochure", sku="MAT-1001", is_sample=False),
            Material(name="CardioPlus 10mg Sample Pack", type="sample", sku="SMP-2001", is_sample=True),
            Material(name="GlycoBalance Clinical Study Reprint", type="study", sku="MAT-1002", is_sample=False),
            Material(name="OncoRelief Patient Leaflet", type="leaflet", sku="MAT-1003", is_sample=False),
        ])
        db.commit()
        print("✓ Seeded sample HCPs and materials")
    finally:
        db.close()
