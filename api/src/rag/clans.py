from sqlmodel import Session, select
from sqlalchemy.orm import defer
from src.models.vampire_v5.clans import Clans, Arquetipes, ClanDisciplines
from datetime import UTC, datetime
import time
from src.utils import update_progress
import argparse

from src.config.config import get_settings
from src.infrastructure.database import Database
from src.integrations.ollama import OllamaEmbeddingService

def compose_clan_article(
        clan: Clans, 
        arquetipes: Arquetipes, #plural
        clanDiscipline: ClanDisciplines #plural
) -> str:
    article = f"{clan.name}\n"
    article += ', '.join(clan.nicknames) + '\n'
    article += f"{clan.description}\n¿Quienes son los {clan.name}?\n{clan.who_are_they}\n"
    article += f"Arquetipos {clan.name}\n"
    for arquetipe in arquetipes:
        article += compose_arquetipe_article(arquetipe)
    article += "Disciplinas\n" if clan.clan_id != 9 else ""
    for discipline in clanDiscipline:
        article += compose_clan_discipline_article(discipline)
    article += f"Prohibición\n{clan.prohibitions}" if clan.clan_id != 9 else ""
    return article

def compose_arquetipe_article(arquetipe: Arquetipes) -> str:
    return f"{arquetipe.title}\n{arquetipe.description}\n"

def compose_clan_discipline_article(clanDiscipline: ClanDisciplines) -> str:
    return f"{clanDiscipline.title}\n{clanDiscipline.description}\n"

def get_first_clan(session: Session) -> Clans | None:
    statement = select(Clans).options(defer(Clans.embedding))
    return session.exec(statement).first()

def get_all_clans(session: Session) -> list[Clans]:
    statement = select(Clans).options(defer(Clans.embedding))
    return list(session.exec(statement).all())

def get_clan_by_name(session: Session, name: str) -> Clans | None:
    statement = select(Clans).where(Clans.name == name).options(defer(Clans.embedding))
    return session.exec(statement).first()

def get_clans_ordered(session: Session) -> list[Clans]:
    statement = select(Clans).order_by(Clans.name).options(defer(Clans.embedding))
    return list(session.exec(statement).all())

def get_arquetipes_by_clan(session: Session, clan_id: int) -> Arquetipes | None:
    statement = select(Arquetipes).where(Arquetipes.clan_id == clan_id).options(defer(Arquetipes.embedding))
    return list(session.exec(statement).all())

def get_all_arquetipes(session: Session) -> list[Arquetipes]:
    statement = select(Arquetipes).options(defer(Arquetipes.embedding))
    return list(session.exec(statement).all())

def get_disciplines_by_clan(session: Session, clan_id: int) -> ClanDisciplines | None:
    statement = select(ClanDisciplines).where(ClanDisciplines.clan_id == clan_id).options(defer(ClanDisciplines.embedding))
    return list(session.exec(statement).all())

def get_all_clan_disciplines(session: Session) -> list[ClanDisciplines]:
    statement = select(ClanDisciplines).options(defer(ClanDisciplines.embedding))
    return list(session.exec(statement).all())

def embbed_all_clans(db: Database, embedder: OllamaEmbeddingService) -> None:
    db.connect()
    try:
        with db.transaction() as session:
            clans = get_all_clans(session)
            total_iterations = len(clans)
            print(f"Embedding all clans, {total_iterations} iterations")
            for i, clan in enumerate(clans):
                start_time = time.time()
                arquetipes = get_arquetipes_by_clan(session, clan.clan_id)
                disciplines = get_disciplines_by_clan(session, clan.clan_id)
                article = compose_clan_article(clan, arquetipes, disciplines)
                clan.updated_by = 'robot'
                clan.updated_at = datetime.now(UTC)
                clan.embedding = embedder.embed(article)
                clan.embedding_model = embedder._model
                clan.embedded_at = datetime.now(UTC)
                session.add(clan)
                update_progress(
                    current=i, 
                    total=total_iterations, 
                    start_time=start_time, 
                    update_interval=1
                )
            update_progress(
                current=total_iterations, 
                total=total_iterations, 
                start_time=time.time(), 
                update_interval=1
            )
            print("")
            session.commit()
    finally:
            db.disconnect()

def embbed_all_arquetipes(db: Database, embedder: OllamaEmbeddingService) -> None:
    db.connect()
    try:
        with db.transaction() as session:
            arquetipes = get_all_arquetipes(session)
            total_iterations = len(arquetipes)
            print(f"Embedding all arquetipes, {total_iterations} iterations")
            for i, arquetipe in enumerate(arquetipes):
                start_time = time.time()
                article = compose_arquetipe_article(arquetipe)
                arquetipe.updated_by = 'robot'
                arquetipe.updated_at = datetime.now(UTC)
                arquetipe.embedding = embedder.embed(article)
                arquetipe.embedding_model = embedder._model
                arquetipe.embedded_at = datetime.now(UTC)
                session.add(arquetipe)
                update_progress(
                    current=i, 
                    total=total_iterations, 
                    start_time=start_time, 
                    update_interval=1
                )
            update_progress(
                current=total_iterations, 
                total=total_iterations, 
                start_time=time.time(), 
                update_interval=1
            )
            print("")
            session.commit()
    finally:
            db.disconnect()

def embbed_all_clan_disciplines(db: Database, embedder: OllamaEmbeddingService) -> None:
    db.connect()
    try:
        with db.transaction() as session:
            disciplines = get_all_clan_disciplines(session)
            total_iterations = len(disciplines)
            print(f"Embedding all arquetipes, {total_iterations} iterations")
            for i, discipline in enumerate(disciplines):
                start_time = time.time()
                article = compose_clan_discipline_article(discipline)
                discipline.updated_by = 'robot'
                discipline.updated_at = datetime.now(UTC)
                discipline.embedding = embedder.embed(article)
                discipline.embedding_model = embedder._model
                discipline.embedded_at = datetime.now(UTC)
                session.add(discipline)
                update_progress(
                    current=i, 
                    total=total_iterations, 
                    start_time=start_time, 
                    update_interval=1
                )
            update_progress(
                current=total_iterations, 
                total=total_iterations, 
                start_time=time.time(), 
                update_interval=1
            )
            print("")
            session.commit()
    finally:
            db.disconnect()

if __name__ == "__main__":

    settings = get_settings()
    embedder = OllamaEmbeddingService(settings)
    db = Database(settings)
    embbed_all_clans(db, embedder)
    embbed_all_arquetipes(db, embedder)
    embbed_all_clan_disciplines(db, embedder)


    