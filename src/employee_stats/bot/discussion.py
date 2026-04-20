# coding=utf-8

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InputMediaPhoto, InputMediaVideo, ReactionTypeEmoji

from src.config import config
from src.advertisment import load_advertisements


router = Router()
router.message.filter(
    # Only messages sent to discussion chat
    F.chat.id == config.telegram.discussion_chat_id,
)


@router.message(F.forward_from_chat.id == config.telegram.chat_id)
async def handle_discussion(message: Message) -> None:
    """
    Handle messages forwarded from channel to discussion group.
    """

    for advertisement in load_advertisements():
        if advertisement.message_id == message.forward_from_message_id:
            # Found forwarded advertisement
            break
    else:
        # Unknown message
        return None

    # Prepare media to be sent
    all_media: list[InputMediaPhoto | InputMediaVideo] = []
    all_media += [InputMediaPhoto(media=photo_url) for photo_url in advertisement.photo_urls]
    all_media += [InputMediaVideo(media=video_url) for video_url in advertisement.video_urls]

    for offset in range(0, len(all_media), 10):
        # Prepare each media page
        media = all_media[offset:offset + 10]
        kwargs = {"reply_to_message_id": message.message_id}

        if len(media) > 1:
            # Few photos/videos => send as media group
            await message.answer_media_group(media=media, **kwargs)

        elif isinstance(media[0], InputMediaPhoto):
            # Single photo
            await message.answer_photo(photo=media[0].media, **kwargs)

        elif isinstance(media[0], InputMediaVideo):
            # Single video
            await message.answer_video(video=media[0].media, **kwargs)


@router.message(Command("media"))
async def post_discussion_media(message: Message) -> None:
    """
    Post media to discussion when user replies with /media command
    """

    if reply := message.reply_to_message:
        if chat := reply.forward_from_chat:
            if chat.id == config.telegram.chat_id:
                # Replied message is forwarded from channel, so we can handle it as advertisement
                await message.react([ReactionTypeEmoji(emoji="🫡")])
                await handle_discussion(reply)
