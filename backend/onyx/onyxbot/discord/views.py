import discord
from sqlalchemy import select

from onyx.configs.constants import MessageType
from onyx.configs.constants import SearchFeedbackType
from onyx.db.engine import get_session_with_tenant
from onyx.db.feedback import create_chat_message_feedback
from onyx.db.feedback import create_doc_retrieval_feedback
from onyx.db.models import ChatMessage
from onyx.utils.logger import setup_logger

logger = setup_logger()


class BaseFeedbackView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.feedback_message = None

    async def process_feedback(
        self,
        interaction: discord.Interaction,
        is_positive: bool,
        positive_button_id: str,
        negative_button_id: str,
    ):
        try:
            for child in self.children:
                if child.custom_id == positive_button_id:
                    child.style = (
                        discord.ButtonStyle.green
                        if is_positive
                        else discord.ButtonStyle.grey
                    )
                    child.disabled = is_positive
                elif child.custom_id == negative_button_id:
                    child.style = (
                        discord.ButtonStyle.red
                        if not is_positive
                        else discord.ButtonStyle.grey
                    )
                    child.disabled = not is_positive

            await interaction.message.edit(view=self)

            response_message = await self.get_feedback_message(is_positive)

            if self.feedback_message:
                try:
                    await self.feedback_message.edit(content=response_message)
                    await interaction.response.defer()
                except Exception:
                    self.feedback_message = await interaction.response.send_message(
                        response_message, ephemeral=True
                    )
            else:
                self.feedback_message = await interaction.response.send_message(
                    response_message, ephemeral=True
                )

            await self.handle_feedback(interaction, is_positive)

        except Exception:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Sorry, there was an error processing your feedback.",
                    ephemeral=True,
                )

    async def get_feedback_message(self, is_positive: bool) -> str:
        """Override this method to provide specific feedback messages"""
        raise NotImplementedError

    async def handle_feedback(
        self, interaction: discord.Interaction, is_positive: bool
    ):
        """Override this method to handle feedback storage/processing"""
        raise NotImplementedError


class FeedbackView(BaseFeedbackView):
    def __init__(self, message_id: str):
        super().__init__()
        self.message_id = str(message_id)

    async def get_feedback_message(self, is_positive: bool) -> str:
        return (
            "Thanks for the positive feedback!"
            if is_positive
            else "Thanks for the feedback. We'll work on improving!"
        )

    async def handle_feedback(
        self, interaction: discord.Interaction, is_positive: bool
    ):
        if not interaction.message or not interaction.message.reference:
            return

        try:
            original_msg = await interaction.channel.fetch_message(
                interaction.message.reference.message_id
            )
            if interaction.user.id != original_msg.author.id:
                await interaction.response.send_message(
                    "Only the person who asked the question can provide feedback.",
                    ephemeral=True,
                )
                return
        except Exception as e:
            logger.error(f"Error fetching original message: {e}")
            return

        try:
            with get_session_with_tenant(None) as db_session:
                stmt = (
                    select(ChatMessage)
                    .where(
                        ChatMessage.message == interaction.message.content,
                        ChatMessage.message_type == MessageType.ASSISTANT,
                    )
                    .order_by(ChatMessage.time_sent.desc())
                )

                chat_message = db_session.execute(stmt).first()

                if not chat_message:
                    return

                create_chat_message_feedback(
                    is_positive=is_positive,
                    feedback_text="",
                    chat_message_id=chat_message[0].id,
                    user_id=None,
                    db_session=db_session,
                )
        except Exception as e:
            logger.error(f"Database error storing feedback: {e}")
            raise

    @discord.ui.button(emoji="👍", style=discord.ButtonStyle.grey, custom_id="helpful")
    async def helpful_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.process_feedback(interaction, True, "helpful", "not_helpful")

    @discord.ui.button(
        emoji="👎", style=discord.ButtonStyle.grey, custom_id="not_helpful"
    )
    async def not_helpful_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.process_feedback(interaction, False, "helpful", "not_helpful")


class DocumentFeedbackView(BaseFeedbackView):
    def __init__(self, document_id: str):
        super().__init__()
        self.document_id = document_id

    async def get_feedback_message(self, is_positive: bool) -> str:
        return (
            "Thanks for the document feedback!"
            if is_positive
            else "Thanks for the feedback. We'll note this document might need improvement!"
        )

    async def handle_feedback(
        self, interaction: discord.Interaction, is_positive: bool
    ):
        try:
            with get_session_with_tenant(None) as db_session:
                feedback_type = (
                    SearchFeedbackType.ENDORSE
                    if is_positive
                    else SearchFeedbackType.REJECT
                )

                create_doc_retrieval_feedback(
                    message_id=None,
                    document_id=self.document_id,
                    document_rank=1,
                    db_session=db_session,
                    clicked=True,
                    feedback=feedback_type,
                )

        except Exception as e:
            logger.error(f"Error storing document feedback: {e}")
            raise

    @discord.ui.button(
        emoji="👍", style=discord.ButtonStyle.grey, custom_id="doc_helpful"
    )
    async def doc_helpful_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.process_feedback(interaction, True, "doc_helpful", "doc_not_helpful")

    @discord.ui.button(
        emoji="👎", style=discord.ButtonStyle.grey, custom_id="doc_not_helpful"
    )
    async def doc_not_helpful_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.process_feedback(
            interaction, False, "doc_helpful", "doc_not_helpful"
        )


class ContinueOnOnyxView(discord.ui.View):
    def __init__(self, chat_session_id: str):
        super().__init__()
        self.add_item(
            discord.ui.Button(
                label="Continue on Onyx",
                style=discord.ButtonStyle.link,
                url=f"https://onyx.app/chat/{chat_session_id}",
            )
        )
