from typing import Optional

import discord

from onyx.utils.logger import setup_logger

logger = setup_logger()


async def update_emote_react(
    channel: discord.TextChannel | discord.Thread | discord.DMChannel,
    message: discord.Message,
    emote: str,
    remove: bool = False,
) -> None:
    try:
        emoji_map = {
            ":thinking:": "🤔",
            ":white_check_mark:": "✅",
            ":hourglass_flowing_sand:": "⏳",
            ":x:": "❌",
            ":brain:": "🧠",
        }

        discord_emoji = emoji_map.get(emote, emote)

        if remove:
            if isinstance(channel, discord.DMChannel):
                await message.remove_reaction(discord_emoji, channel.me)
            else:
                await message.remove_reaction(discord_emoji, channel.guild.me)
        else:
            await message.add_reaction(discord_emoji)
    except Exception as e:
        logger.error(f"Failed to update reaction: {e}")


async def send_message_response(
    channel: discord.TextChannel | discord.Thread | discord.DMChannel,
    text: str,
    thread_ts: Optional[str] = None,
    blocks: Optional[list] = None,
) -> None:
    try:
        if thread_ts:
            try:
                message = await channel.fetch_message(int(thread_ts))
                await message.reply(content=text)
            except Exception as e:
                logger.error(f"Failed to fetch message: {e}")
                await channel.send(content=text)
        else:
            await channel.send(content=text)
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
