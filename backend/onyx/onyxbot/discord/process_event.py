from datetime import datetime
from datetime import timezone

import discord
import timeago
from discord.ext import commands
from sqlalchemy import select

from onyx.chat.chat_utils import prepare_chat_message_request
from onyx.chat.models import StreamingError
from onyx.chat.models import ThreadMessage
from onyx.chat.process_message import stream_chat_message_objects
from onyx.configs.constants import MessageType
from onyx.configs.onyxbot_configs import DANSWER_BOT_NUM_DOCS_TO_DISPLAY
from onyx.configs.onyxbot_configs import DANSWER_BOT_REPHRASE_MESSAGE
from onyx.context.search.models import BaseFilters
from onyx.context.search.models import OptionalSearchSetting
from onyx.context.search.models import RetrievalDetails
from onyx.db.engine import get_session_with_tenant
from onyx.db.models import ChatMessage
from onyx.onyxbot.discord.models import DiscordMessageInfo
from onyx.onyxbot.discord.utils import update_emote_react
from onyx.onyxbot.discord.views import ContinueOnOnyxView
from onyx.onyxbot.discord.views import DocumentFeedbackView
from onyx.onyxbot.discord.views import FeedbackView
from onyx.onyxbot.slack.utils import rephrase_slack_message
from onyx.utils.logger import setup_logger

logger = setup_logger()

# In rare cases, some users have been experiencing a massive amount of trivial messages
# Adding this to avoid exploding LLM costs while we track down the cause.
_DISCORD_GREETINGS_TO_IGNORE = {
    "Welcome back!",
    "It's going to be a great day.",
    "Salutations!",
    "Greetings!",
    "Feeling great!",
    "Hi there",
    ":wave:",
}


def prefilter_message(message: discord.Message) -> bool:
    """Filter out messages that shouldn't be processed"""
    if not message.content:
        logger.warning("Cannot respond to empty message - skipping")
        return False

    if message.author.bot:
        logger.info("Ignoring message from bot")
        return False

    if message.content in _DISCORD_GREETINGS_TO_IGNORE:
        logger.error(f"Ignoring greeting message: '{message.content}'")
        return False

    return True


def get_thread_messages(message: discord.Message) -> list[ThreadMessage]:
    """Get all messages in the thread if message is in one"""
    messages = []

    # If message is in a thread, get previous messages
    if isinstance(message.channel, discord.Thread):
        # TODO: Implement proper thread history fetching
        # For now, just add the current message
        messages.append(
            ThreadMessage(
                message=message.content,
                sender=str(message.author),
                role=MessageType.USER,
            )
        )
    else:
        messages.append(
            ThreadMessage(
                message=message.content,
                sender=str(message.author),
                role=MessageType.USER,
            )
        )

    return messages


def build_message_info(
    message: discord.Message,
    bot: commands.Bot,
) -> DiscordMessageInfo:
    # Check if bot was mentioned or if it's a DM
    is_bot_mention = bot.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)

    # Get message content, removing bot mention if present
    content = message.content
    if is_bot_mention:
        content = content.replace(f"<@{bot.user.id}>", "").strip()

    # Get channel and thread IDs
    str(message.channel.id)
    thread_id = str(message.thread.id) if message.thread else None

    # Build thread messages
    thread_messages = [
        ThreadMessage(
            message=content,
            message_type=MessageType.USER,
            message_id=str(message.id),
        )
    ]

    return DiscordMessageInfo(
        thread_messages=thread_messages,
        channel_to_respond=str(message.channel.id),
        msg_to_respond=str(message.id),
        thread_to_respond=thread_id,
        bypass_filters=is_bot_mention or is_dm,
        is_bot_msg=message.author.bot,
        is_bot_dm=is_dm,
        sender_id=str(message.author.id),
        email=f"{message.author.id}@discord.com",
        chat_session_id=str(message.id),
    )


async def handle_regular_answer(
    message: discord.Message,
    message_info: DiscordMessageInfo,
    bot: commands.Bot,
) -> None:
    try:
        channel = bot.get_channel(int(message_info.channel_to_respond))
        if not channel:
            logger.error(f"Could not find channel {message_info.channel_to_respond}")
            return

        await update_emote_react(
            channel,
            message,
            ":thinking:",
        )

        if message_info.thread_messages[-1].message in _DISCORD_GREETINGS_TO_IGNORE:
            return

        content = message_info.thread_messages[-1].message
        if DANSWER_BOT_REPHRASE_MESSAGE:
            try:
                content = rephrase_slack_message(content)
            except Exception as e:
                logger.error(f"Error rephrasing message: {e}")

        with get_session_with_tenant(None) as db_session:
            answer_request = prepare_chat_message_request(
                message_text=content,
                user=None,
                persona_id=None,
                persona_override_config=None,
                prompt=None,
                message_ts_to_respond_to=message_info.msg_to_respond,
                retrieval_details=RetrievalDetails(
                    run_search=OptionalSearchSetting.ALWAYS,
                    real_time=False,
                    filters=BaseFilters(),
                    enable_auto_detect_filters=True,
                ),
                rerank_settings=None,
                db_session=db_session,
            )

            try:
                generator = stream_chat_message_objects(
                    answer_request,
                    user=None,
                    db_session=db_session,
                )
                answer = ""
                documents = []

                for chunk in generator:
                    if isinstance(chunk, StreamingError):
                        raise Exception(f"Error getting answer from LLM: {chunk.error}")

                    if hasattr(chunk, "answer_piece"):
                        answer += chunk.answer_piece

                    if hasattr(chunk, "context_docs"):
                        if hasattr(chunk.context_docs, "top_documents"):
                            for doc in chunk.context_docs.top_documents:
                                if any(
                                    onyx_doc in doc.semantic_identifier.lower()
                                    for onyx_doc in [
                                        "customer support",
                                        "enterprise search",
                                        "operations",
                                        "ai platform",
                                        "sales",
                                        "use cases",
                                    ]
                                ):
                                    continue
                                documents.append(doc)

                if not answer.strip():
                    raise Exception("No response content generated")

                embeds = []
                if documents:
                    doc_embed = discord.Embed(
                        title="Reference Documents", color=0x00FF00
                    )

                    seen_docs_identifiers = set()
                    included_docs = 0

                    for doc in documents:
                        if doc.document_id in seen_docs_identifiers:
                            continue
                        seen_docs_identifiers.add(doc.document_id)

                        title = doc.semantic_identifier[:70]
                        if len(doc.semantic_identifier) > 70:
                            title += "..."

                        value_parts = []
                        source_type = str(doc.source_type).replace(
                            "DocumentSource.", ""
                        )
                        value_parts.append(f"Source: {source_type}")

                        if doc.updated_at:
                            time_ago = timeago.format(
                                doc.updated_at, datetime.now(timezone.utc)
                            )
                            value_parts.append(f"Updated {time_ago}")

                        if doc.primary_owners and len(doc.primary_owners) > 0:
                            value_parts.append(f"By {doc.primary_owners[0]}")

                        if doc.link:
                            value_parts.append(f"[View Document]({doc.link})")

                        if doc.match_highlights:
                            highlights = [
                                h.strip(" .") for h in doc.match_highlights if h.strip()
                            ]
                            if highlights:
                                highlight = highlights[0]
                                highlight = " ".join(highlight.split())
                                highlight = highlight.replace("<hi>", "**").replace(
                                    "</hi>", "**"
                                )
                                if len(highlight) > 300:
                                    highlight = highlight[:297] + "..."
                                value_parts.append(f"\nRelevant excerpt:\n{highlight}")

                        field_value = "\n".join(value_parts)
                        if len(field_value) > 1024:
                            field_value = field_value[:1021] + "..."

                        doc_embed.add_field(
                            name=title,
                            value=field_value or "No preview available",
                            inline=False,
                        )

                        included_docs += 1
                        if included_docs >= DANSWER_BOT_NUM_DOCS_TO_DISPLAY:
                            break

                    embeds.append(doc_embed)

                view = FeedbackView(str(message_info.msg_to_respond))

                try:
                    await channel.send(content=answer, reference=message, view=view)

                    with get_session_with_tenant(None) as db_session:
                        stmt = (
                            select(ChatMessage)
                            .where(
                                ChatMessage.message == answer,
                                ChatMessage.message_type == MessageType.ASSISTANT,
                            )
                            .order_by(ChatMessage.time_sent.desc())
                        )

                        chat_message = db_session.execute(stmt).first()
                        if chat_message:
                            continue_view = ContinueOnOnyxView(
                                str(chat_message[0].chat_session_id)
                            )
                            await channel.send(view=continue_view)

                    if embeds:
                        doc_view = DocumentFeedbackView(str(documents[0].document_id))
                        await channel.send(embeds=embeds, view=doc_view)
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")

                    await update_emote_react(
                        channel,
                        message,
                        ":thinking:",
                        remove=True,
                    )
                    await update_emote_react(
                        channel,
                        message,
                        ":white_check_mark:",
                    )

                except Exception:
                    await message.reply(
                        "I apologize, but I encountered an error while processing your request. Please try again later."
                    )
                    return

            except Exception:
                await message.reply(
                    "I apologize, but I encountered an error while processing your request. Please try again later."
                )
                return

    except Exception:
        await message.reply(
            "I apologize, but I encountered an error while processing your request. Please try again later."
        )


async def process_message(message: discord.Message, bot: commands.Bot) -> None:
    # Don't respond to our own messages
    if message.author == bot.user:
        return

    # Only respond to mentions or DMs
    if bot.user in message.mentions or isinstance(message.channel, discord.DMChannel):
        message_info = build_message_info(message, bot)
        await handle_regular_answer(message, message_info, bot)


def create_process_discord_event():
    """Creates the main event processing function"""

    async def process_discord_event(message: discord.Message) -> None:
        try:
            await process_message(
                message,
                message.guild.me
                if message.guild
                else message.author.mutual_guilds[0].me,
            )
        except Exception:
            logger.exception("Failed to process discord event")

    return process_discord_event
