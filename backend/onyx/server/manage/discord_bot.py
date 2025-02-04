from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from onyx.auth.users import current_admin_user
from onyx.configs.constants import MilestoneRecordType
from onyx.db.constants import DISCORD_BOT_PERSONA_PREFIX
from onyx.db.discord_bot import fetch_discord_bot
from onyx.db.discord_bot import fetch_discord_bots
from onyx.db.discord_bot import insert_discord_bot
from onyx.db.discord_bot import remove_discord_bot
from onyx.db.discord_bot import update_discord_bot
from onyx.db.discord_channel_config import create_discord_channel_persona
from onyx.db.discord_channel_config import fetch_discord_channel_config
from onyx.db.discord_channel_config import fetch_discord_channel_configs
from onyx.db.discord_channel_config import insert_discord_channel_config
from onyx.db.discord_channel_config import remove_discord_channel_config
from onyx.db.discord_channel_config import update_discord_channel_config
from onyx.db.engine import get_current_tenant_id
from onyx.db.engine import get_session
from onyx.db.models import ChannelConfig
from onyx.db.models import User
from onyx.db.persona import get_persona_by_id
from onyx.onyxbot.discord.config import validate_channel_name
from onyx.server.manage.models import DiscordBot
from onyx.server.manage.models import DiscordBotCreationRequest
from onyx.server.manage.models import DiscordChannelConfig
from onyx.server.manage.models import DiscordChannelConfigCreationRequest
from onyx.utils.telemetry import create_milestone_and_report


router = APIRouter(prefix="/manage")


def _form_channel_config(
    db_session: Session,
    discord_channel_config_creation_request: DiscordChannelConfigCreationRequest,
    current_discord_channel_config_id: int | None,
) -> ChannelConfig:
    raw_channel_name = discord_channel_config_creation_request.channel_name
    respond_mention_only = discord_channel_config_creation_request.respond_mention_only
    respond_member_group_list = (
        discord_channel_config_creation_request.respond_member_group_list
    )
    answer_filters = discord_channel_config_creation_request.answer_filters
    follow_up_tags = discord_channel_config_creation_request.follow_up_tags

    if not raw_channel_name:
        raise HTTPException(
            status_code=400,
            detail="Must provide at least one channel name",
        )

    try:
        cleaned_channel_name = validate_channel_name(
            db_session=db_session,
            channel_name=raw_channel_name,
            current_discord_channel_config_id=current_discord_channel_config_id,
            current_discord_bot_id=discord_channel_config_creation_request.discord_bot_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    if respond_mention_only and respond_member_group_list:
        raise ValueError(
            "Cannot set OnyxBot to only respond to mentions only and "
            "also respond to a predetermined set of users."
        )

    channel_config: ChannelConfig = {
        "channel_name": cleaned_channel_name,
    }
    if respond_mention_only is not None:
        channel_config["respond_mention_only"] = respond_mention_only
    if respond_member_group_list:
        channel_config["respond_member_group_list"] = respond_member_group_list
    if answer_filters:
        channel_config["answer_filters"] = answer_filters
    if follow_up_tags is not None:
        channel_config["follow_up_tags"] = follow_up_tags

    channel_config[
        "show_continue_in_web_ui"
    ] = discord_channel_config_creation_request.show_continue_in_web_ui

    channel_config[
        "respond_to_bots"
    ] = discord_channel_config_creation_request.respond_to_bots

    return channel_config


@router.post("/admin/discord-app/channel")
def create_discord_channel_config(
    discord_channel_config_creation_request: DiscordChannelConfigCreationRequest,
    db_session: Session = Depends(get_session),
    _: User | None = Depends(current_admin_user),
) -> DiscordChannelConfig:
    channel_config = _form_channel_config(
        db_session=db_session,
        discord_channel_config_creation_request=discord_channel_config_creation_request,
        current_discord_channel_config_id=None,
    )

    persona_id = None
    if discord_channel_config_creation_request.persona_id is not None:
        persona_id = discord_channel_config_creation_request.persona_id
    elif discord_channel_config_creation_request.document_sets:
        persona_id = create_discord_channel_persona(
            db_session=db_session,
            channel_name=channel_config["channel_name"],
            document_set_ids=discord_channel_config_creation_request.document_sets,
            existing_persona_id=None,
        ).id

    discord_channel_config_model = insert_discord_channel_config(
        discord_bot_id=discord_channel_config_creation_request.discord_bot_id,
        persona_id=persona_id,
        channel_config=channel_config,
        db_session=db_session,
        enable_auto_filters=discord_channel_config_creation_request.enable_auto_filters,
    )
    return DiscordChannelConfig.from_model(discord_channel_config_model)


@router.patch("/admin/discord-app/channel/{discord_channel_config_id}")
def patch_discord_channel_config(
    discord_channel_config_id: int,
    discord_channel_config_creation_request: DiscordChannelConfigCreationRequest,
    db_session: Session = Depends(get_session),
    _: User | None = Depends(current_admin_user),
) -> DiscordChannelConfig:
    channel_config = _form_channel_config(
        db_session=db_session,
        discord_channel_config_creation_request=discord_channel_config_creation_request,
        current_discord_channel_config_id=discord_channel_config_id,
    )

    persona_id = None
    if discord_channel_config_creation_request.persona_id is not None:
        persona_id = discord_channel_config_creation_request.persona_id
    elif discord_channel_config_creation_request.document_sets:
        existing_discord_channel_config = fetch_discord_channel_config(
            db_session=db_session, discord_channel_config_id=discord_channel_config_id
        )
        if existing_discord_channel_config is None:
            raise HTTPException(
                status_code=404,
                detail="Discord channel config not found",
            )

        existing_persona_id = existing_discord_channel_config.persona_id
        if existing_persona_id is not None:
            persona = get_persona_by_id(
                persona_id=existing_persona_id,
                user=None,
                db_session=db_session,
                is_for_edit=False,
            )

            if not persona.name.startswith(DISCORD_BOT_PERSONA_PREFIX):
                # Don't update actual non-discordbot specific personas
                # Since this one specified document sets, we have to create a new persona
                # for this OnyxBot config
                existing_persona_id = None
            else:
                existing_persona_id = existing_discord_channel_config.persona_id

        persona_id = create_discord_channel_persona(
            db_session=db_session,
            channel_name=channel_config["channel_name"],
            document_set_ids=discord_channel_config_creation_request.document_sets,
            existing_persona_id=existing_persona_id,
            enable_auto_filters=discord_channel_config_creation_request.enable_auto_filters,
        ).id

    discord_channel_config_model = update_discord_channel_config(
        db_session=db_session,
        discord_channel_config_id=discord_channel_config_id,
        persona_id=persona_id,
        channel_config=channel_config,
        enable_auto_filters=discord_channel_config_creation_request.enable_auto_filters,
    )
    return DiscordChannelConfig.from_model(discord_channel_config_model)


@router.delete("/admin/discord-app/channel/{discord_channel_config_id}")
def delete_discord_channel_config(
    discord_channel_config_id: int,
    db_session: Session = Depends(get_session),
    user: User | None = Depends(current_admin_user),
) -> None:
    remove_discord_channel_config(
        db_session=db_session,
        discord_channel_config_id=discord_channel_config_id,
        user=user,
    )


@router.get("/admin/discord-app/channel")
def list_discord_channel_configs(
    db_session: Session = Depends(get_session),
    _: User | None = Depends(current_admin_user),
) -> list[DiscordChannelConfig]:
    discord_channel_config_models = fetch_discord_channel_configs(db_session=db_session)
    return [
        DiscordChannelConfig.from_model(discord_channel_config_model)
        for discord_channel_config_model in discord_channel_config_models
    ]


@router.post("/admin/discord-app/bots")
def create_bot(
    discord_bot_creation_request: DiscordBotCreationRequest,
    db_session: Session = Depends(get_session),
    _: User | None = Depends(current_admin_user),
    tenant_id: str | None = Depends(get_current_tenant_id),
) -> DiscordBot:
    discord_bot_model = insert_discord_bot(
        db_session=db_session,
        name=discord_bot_creation_request.name,
        enabled=discord_bot_creation_request.enabled,
        discord_bot_token=discord_bot_creation_request.bot_token,
    )

    create_milestone_and_report(
        user=None,
        distinct_id=tenant_id or "N/A",
        event_type=MilestoneRecordType.CREATED_ONYX_BOT,
        properties=None,
        db_session=db_session,
    )

    return DiscordBot.from_model(discord_bot_model)


@router.patch("/admin/discord-app/bots/{discord_bot_id}")
def patch_bot(
    discord_bot_id: int,
    discord_bot_creation_request: DiscordBotCreationRequest,
    db_session: Session = Depends(get_session),
    _: User | None = Depends(current_admin_user),
) -> DiscordBot:
    discord_bot_model = update_discord_bot(
        db_session=db_session,
        discord_bot_id=discord_bot_id,
        name=discord_bot_creation_request.name,
        enabled=discord_bot_creation_request.enabled,
        discord_bot_token=discord_bot_creation_request.bot_token,
    )
    return DiscordBot.from_model(discord_bot_model)


@router.delete("/admin/discord-app/bots/{discord_bot_id}")
def delete_bot(
    discord_bot_id: int,
    db_session: Session = Depends(get_session),
    _: User | None = Depends(current_admin_user),
) -> None:
    remove_discord_bot(
        db_session=db_session,
        discord_bot_id=discord_bot_id,
    )


@router.get("/admin/discord-app/bots/{discord_bot_id}")
def get_bot_by_id(
    discord_bot_id: int,
    db_session: Session = Depends(get_session),
    _: User | None = Depends(current_admin_user),
) -> DiscordBot:
    discord_bot_model = fetch_discord_bot(
        db_session=db_session,
        discord_bot_id=discord_bot_id,
    )
    return DiscordBot.from_model(discord_bot_model)


@router.get("/admin/discord-app/bots")
def list_bots(
    db_session: Session = Depends(get_session),
    _: User | None = Depends(current_admin_user),
) -> list[DiscordBot]:
    discord_bot_models = fetch_discord_bots(db_session=db_session)
    return [
        DiscordBot.from_model(discord_bot_model)
        for discord_bot_model in discord_bot_models
    ]


@router.get("/admin/discord-app/bots/{bot_id}/config")
def list_bot_configs(
    bot_id: int,
    db_session: Session = Depends(get_session),
    _: User | None = Depends(current_admin_user),
) -> list[DiscordChannelConfig]:
    discord_bot_config_models = fetch_discord_channel_configs(
        db_session=db_session, discord_bot_id=bot_id
    )
    return [
        DiscordChannelConfig.from_model(discord_bot_config_model)
        for discord_bot_config_model in discord_bot_config_models
    ]
