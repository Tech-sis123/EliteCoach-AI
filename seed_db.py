from core.database import SessionLocal, engine
from models.models import Subject, Base

def seed_database():
    print("Ensuring tables are created...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        subjects = db.query(Subject).all()
        print(f"Current subject count: {len(subjects)}")
        
        # Check if Mathematics (ID 20) specifically exists
        math_exists = db.query(Subject).filter(Subject.id == 20).first()
        
        if not math_exists:
            print("Seeding essential subjects...")
            # We use merge or check existence to avoid primary key collisions if ID 1/2 exist but 20 doesn't
            default_subjects = [
                Subject(id=20, name="Mathematics", description="General mathematics courses", difficulty_level="intermediate"),
                Subject(id=1, name="Physics", description="Introduction to Physics", difficulty_level="beginner"),
                Subject(id=2, name="Chemistry", description="Chemical reactions and properties", difficulty_level="intermediate")
            ]
            
            for sub in default_subjects:
                existing = db.query(Subject).filter(Subject.id == sub.id).first()
                if not existing:
                    db.add(sub)
            
            db.commit()
            print("Seeding complete.")
        else:
            print("Database already contains required subjects.")
            
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
