from sqlmodel import Session, select

from src.models.vampire_v5.clans import Clans
from src.models.vampire_v5.disciplines import ClanDisciplines


def get_disciplines_by_clan_name(session: Session, name: str) -> list[tuple[Clans, ClanDisciplines]]:
    statement = (
        select(Clans, ClanDisciplines)
        .join(ClanDisciplines, ClanDisciplines.clan_id == Clans.clan_id)
        .where(Clans.name == name)
    )
    return list(session.exec(statement).all())

def get_discipline_titles_by_clan(session: Session, clan_id: int) -> list[str]:
    statement = (
        select(ClanDisciplines.title)
        .join(Clans, Clans.clan_id == ClanDisciplines.clan_id)
        .where(Clans.clan_id == clan_id)
    )
    return list(session.exec(statement).all())