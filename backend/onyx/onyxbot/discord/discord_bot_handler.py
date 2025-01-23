import asyncio
import os
import signal
import sys
from threading import Event
from types import FrameType
from typing import Dict
from typing import Set

import discord
from discord.ext import commands
from prometheus_client import Gauge
from prometheus_client import start_http_server
from sqlalchemy.orm import Session

from onyx.db.engine import get_session_with_tenant
from onyx.db.models import DiscordBot
from onyx.onyxbot.discord.process_event import process_message
from onyx.utils.logger import setup_logger

logger = setup_logger()

active_tenants_gauge = Gauge(
    "active_tenants",
    "Number of active tenants handled by this pod",
    ["namespace", "pod"],
)


class OnyxDiscordBot(commands.Bot):
    def __init__(
        self,
        discord_bot_id: int,
        tenant_id: str | None = None,
    ):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        self.discord_bot_id = discord_bot_id
        self.tenant_id = tenant_id

    async def setup_hook(self) -> None:
        await self.tree.sync()
        logger.info("Bot commands synced")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user.name} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="for your questions"
            )
        )

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        if self.user in message.mentions or isinstance(
            message.channel, discord.DMChannel
        ):
            await process_message(message, self)


class DiscordbotHandler:
    def __init__(self) -> None:
        logger.info("Initializing DiscordbotHandler")
        self.tenant_ids: Set[str | None] = set()
        self.discord_clients: Dict[str | None, OnyxDiscordBot] = {}

        self.running = True
        self.pod_id = self.get_pod_id()
        self._shutdown_event = Event()
        logger.info(f"Pod ID: {self.pod_id}")

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

        # Start Prometheus metrics server
        start_http_server(8000)

    def get_pod_id(self) -> str:
        return os.environ.get("HOSTNAME", "unknown_pod")

    def run(self):
        """Main method to run the bot"""
        try:
            token = os.environ.get("DISCORD_BOT_TOKEN")
            if not token:
                raise ValueError("DISCORD_BOT_TOKEN environment variable is not set")

            with get_session_with_tenant(None) as db_session:
                discord_bot = create_discord_bot_if_not_exists(db_session, token)

                self.main_bot = OnyxDiscordBot(
                    discord_bot_id=discord_bot.id,
                    tenant_id=None,
                )

                logger.info(f"Starting Discord bot: {discord_bot.name}")
                self.main_bot.run(discord_bot.discord_bot_token)

        except Exception as e:
            logger.exception(f"Error running Discord bot: {e}")
        finally:
            self.shutdown(None, None)

    def shutdown(
        self,
        signum: int | None,
        frame: FrameType | None,
    ) -> None:
        if not self.running:
            return

        logger.info("Shutting down gracefully")
        self.running = False
        self._shutdown_event.set()

        if hasattr(self, "main_bot"):
            asyncio.run(self.main_bot.close())

        logger.info("Shutdown complete")
        sys.exit(0)


def create_discord_bot_if_not_exists(
    db_session: Session,
    token: str,
) -> DiscordBot:
    """Create or get Discord bot entry in database"""
    discord_bot = (
        db_session.query(DiscordBot).filter(DiscordBot.enabled.is_(True)).first()
    )

    if not discord_bot:
        logger.info("Creating new Discord bot entry in database")
        discord_bot = DiscordBot(
            name="Onyx Discord Bot",
            discord_bot_token=token,
            enabled=True,
        )
        db_session.add(discord_bot)
        db_session.commit()
        logger.info("Created Discord bot entry successfully")

    return discord_bot
