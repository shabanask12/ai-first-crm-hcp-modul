from database import SessionLocal, engine, Base
import models

def seed_database():
    # Recreate tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(models.HCP).first() is not None:
            print("Database already seeded.")
            return

        print("Seeding database...")

        # Create HCPs
        hcp1 = models.HCP(name="Dr. John Smith", specialty="Cardiology", hospital="Metro Health Hospital", email="john.smith@metrohealth.com")
        hcp2 = models.HCP(name="Dr. Alice Sharma", specialty="Oncology", hospital="City Cancer Center", email="alice.sharma@citycancer.org")
        hcp3 = models.HCP(name="Dr. Robert Chen", specialty="Pediatrics", hospital="St. Jude Hospital", email="robert.chen@stjude.org")
        hcp4 = models.HCP(name="Dr. Sarah Jenkins", specialty="Endocrinology", hospital="Valley Medical Clinic", email="sarah.jenkins@valleymed.com")
        hcp5 = models.HCP(name="Dr. David Patel", specialty="Neurology", hospital="Brain & Spine Institute", email="david.patel@brainspine.com")

        db.add_all([hcp1, hcp2, hcp3, hcp4, hcp5])
        db.commit()

        # Create Products
        prod1 = models.ProductInfo(name="OncoBoost Phase III Trial Report", description="Detailed clinical results for OncoBoost in lung cancer patients.", material_type="PDF", stock=100)
        prod2 = models.ProductInfo(name="CardioShield 10mg Patient Samples", description="CardioShield starter pack samples for hypertension patients.", material_type="Sample", stock=50)
        prod3 = models.ProductInfo(name="EndoBalance Educational Pamphlet", description="Patient education brochure for diabetes management.", material_type="Brochure", stock=500)
        prod4 = models.ProductInfo(name="NeuroGlow Clinical Study Summary", description="Short clinical summary of NeuroGlow for Alzheimer's patients.", material_type="PDF", stock=200)

        db.add_all([prod1, prod2, prod3, prod4])
        db.commit()

        # Create a sample interaction
        interaction1 = models.Interaction(
            hcp_id=hcp2.id,
            date="2026-07-09",
            time="14:30",
            type="Meeting",
            attendees="Dr. Alice Sharma, Rep Alex",
            topics="Discussed OncoBoost Phase III efficacy and safety profiles.",
            sentiment="Positive",
            outcomes="Dr. Sharma is very interested in the trial results. She requested a copy of the report.",
            follow_ups="Send OncoBoost Phase III Trial Report PDF. Follow up in 1 week."
        )
        interaction1.materials.append(prod1)
        db.add(interaction1)

        # Create a sample task
        task1 = models.Task(
            hcp_id=hcp2.id,
            description="Send OncoBoost Phase III Trial Report PDF",
            due_date="2026-07-12",
            status="Pending"
        )
        db.add(task1)
        db.commit()

        print("Database seeded successfully.")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
