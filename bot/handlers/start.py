from maxapi import Router
from maxapi.filters.command import CommandStart
from maxapi.types import MessageCreated, BotStarted


router = Router()

@router.bot_started()
async def bot_started_handler(event: BotStarted):
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="Привет!"
    )

@router.message_created(CommandStart())
async def start_handler(event: MessageCreated):
    await event.message.answer("Привет!")