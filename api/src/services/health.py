from src.infrastructure.database import Database


class HealthService:
    def __init__(self, database: Database) -> None:
        self._database = database

    def database_status(self) -> dict[str, str]:
        try:
            self._database.ping()
        except Exception:
            return {"status": "not_ready", "database": "unavailable"}

        return {"status": "ready", "database": "available"}
