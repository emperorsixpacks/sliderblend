import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

from sliderblend.internal.storage import get_storage_provider
from sliderblend.pkg import MAX_FILE_SIZE, FilebaseSettings, TelegramSettings
from sliderblend.pkg.logger import get_logger
from sliderblend.pkg.utils import ValidFileType, file_size_mb, sanitize_filename

logger = get_logger(__name__)

telegram_settings = TelegramSettings()

dp = Dispatcher()
storage_settings = FilebaseSettings()

storage_provider = get_storage_provider("filebase", storage_settings)

bot = Bot(token=telegram_settings.telegram_bot_token)


@dp.message(F.document)
async def handle_document(message: Message):
    logger.info("Recived new request")
    user = message.from_user
    document_ = message.document
    response_message = await message.reply(f"Processing Document {document_.file_name}")
    if not ValidFileType.is_valid(document_.mime_type):
        logger.debug("Invalid file type could not uplaod")
        await response_message.edit_text(
            f"Error processing document: {document_.file_name} not a valid file type"
        )

    if MAX_FILE_SIZE < file_size_mb(document_.file_size):
        logger.debug("File to large could not upload")
        await response_message.edit_text(
            f"Error processing document: {document_.file_name} is too large. Max file size is 10mb"
        )

    file_info = await bot.get_file(document_.file_id)
    document_name = sanitize_filename(document_.file_name)
    file_name = f"user:{user.id}/document:{document_name}"
    file_bytes_ = await bot.download_file(file_info.file_path)
    _file, err = storage_provider.upload_bytes(file_bytes_, file_name, "documents")
    if err:
        logger.error(err)
        await response_message.edit_text(
            f"Error processing document: {document_.file_name} server error"
        )
    return


async def main() -> None:
    logger.log("Starting polling")
    await dp.start_polling(bot)
    logger.log("Stopped polling")


if __name__ == "__main__":
    asyncio.run(main())

# TODO we need to add an html parser for more interactivity
