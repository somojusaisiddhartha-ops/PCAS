import csv
import logging
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.project import Project

logger = logging.getLogger(__name__)


class DatasetService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def sync_from_csv(self, db: Session) -> None:
        csv_path = Path(self.settings.dataset_csv)
        if not csv_path.exists():
            logger.warning("Dataset CSV not found at %s. Skipping seed.", csv_path)
            return

        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            projects = [
                Project(
                    title=(row.get("title") or "").strip(),
                    abstract=(row.get("abstract") or "").strip(),
                    domain=(row.get("domain") or "General").strip(),
                    year=int(row.get("year") or 0),
                )
                for row in reader
                if (row.get("title") or "").strip() and (row.get("abstract") or "").strip()
            ]

        if not projects:
            logger.warning("No valid projects found in dataset CSV.")
            return

        db.execute(delete(Project))
        db.add_all(projects)
        db.commit()
        logger.info("Synchronized %s project records from %s.", len(projects), csv_path)

    def fetch_all_projects(self, db: Session) -> list[Project]:
        return list(db.scalars(select(Project).order_by(Project.id)).all())
