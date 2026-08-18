from sqlmodel import Session, text


class HealthService:
    @staticmethod
    def check_database(db: Session) -> dict[str, str]:
        try:
            db.exec(text("SELECT 1")).one()
            return {"status": "healthy"}
        except Exception:
            return {"status": "not_responding"}