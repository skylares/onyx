from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from onyx.db.models import DiscordBot


def insert_discord_bot(
    db_session: Session,
    name: str,
    enabled: bool,
    discord_bot_token: str,
) -> DiscordBot:
    discord_bot = DiscordBot(
        name=name,
        enabled=enabled,
        discord_bot_token=discord_bot_token,
    )
    db_session.add(discord_bot)
    db_session.commit()
    return discord_bot


def update_discord_bot(
    db_session: Session,
    discord_bot_id: int,
    name: str,
    enabled: bool,
    discord_bot_token: str,
) -> DiscordBot:
    discord_bot = db_session.scalar(
        select(DiscordBot).where(DiscordBot.id == discord_bot_id)
    )
    if discord_bot is None:
        raise ValueError(f"Unable to find Discord Bot with ID {discord_bot_id}")

    discord_bot.name = name
    discord_bot.enabled = enabled
    discord_bot.discord_bot_token = discord_bot_token
    db_session.commit()
    return discord_bot


def fetch_discord_bot(
    db_session: Session,
    discord_bot_id: int,
) -> DiscordBot:
    discord_bot = db_session.scalar(
        select(DiscordBot).where(DiscordBot.id == discord_bot_id)
    )
    if discord_bot is None:
        raise ValueError(f"Unable to find Discord Bot with ID {discord_bot_id}")
    return discord_bot


def remove_discord_bot(
    db_session: Session,
    discord_bot_id: int,
) -> None:
    discord_bot = fetch_discord_bot(
        db_session=db_session,
        discord_bot_id=discord_bot_id,
    )

    db_session.delete(discord_bot)
    db_session.commit()


def fetch_discord_bots(db_session: Session) -> Sequence[DiscordBot]:
    return db_session.scalars(select(DiscordBot)).all()
