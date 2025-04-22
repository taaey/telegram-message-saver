import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📌 Forward messages to save with source info!\n"
        "Media files will be saved in original format.",
        parse_mode='Markdown'
    )

async def save_to_saved_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        message = update.message
        timestamp = message.date
        
        # Initialize metadata
        metadata = []
        text_content = message.text or message.caption or ""
        
        # Process forwarding info
        if hasattr(message, 'forward_origin') and message.forward_origin:
            origin = message.forward_origin
            if hasattr(origin, 'sender_chat') and origin.sender_chat:
                chat = origin.sender_chat
                source = getattr(chat, 'title', 'Unknown Channel')
                if hasattr(chat, 'username'):
                    source += f" (@{chat.username})"
                metadata.append(f"Source: {source}")
            if hasattr(origin, 'date'):
                timestamp = origin.date
                metadata.append(f"Original post: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        metadata.append(f"Saved at: {message.date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Handle different message types
        if message.photo:
            # PHOTO HANDLING (saves as JPEG)
            file = await message.photo[-1].get_file()
            filename = f"photo_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
            await file.download_to_drive(filename)
            await context.bot.send_document(
                chat_id=user.id,
                document=filename,
                caption="\n".join([text_content, *metadata]) if text_content else "\n".join(metadata)
            )
            os.remove(filename)
        
        elif message.document:
            # DOCUMENT HANDLING (preserves original format)
            file = await message.document.get_file()
            ext = os.path.splitext(message.document.file_name or "file.bin")[1]
            filename = f"doc_{timestamp.strftime('%Y%m%d_%H%M%S')}{ext}"
            await file.download_to_drive(filename)
            await context.bot.send_document(
                chat_id=user.id,
                document=filename,
                caption="\n".join([text_content, *metadata]) if text_content else "\n".join(metadata)
            )
            os.remove(filename)
        
        # TEXT HANDLING
        if text_content or (not message.photo and not message.document):
            filename = f"text_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"{text_content}\n\n---\n" + "\n".join(metadata))
            await context.bot.send_document(
                chat_id=user.id,
                document=filename,
                caption="Text content" if message.photo or message.document else None
            )
            os.remove(filename)
        
        await update.message.reply_text("✅ Saved successfully!")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text("❌ Failed to save content")

if __name__ == '__main__':
    application = ApplicationBuilder().token("7576603860:AAHsoSj_0BP-QgURj6MDwlp9-CRIurnezC0").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.TEXT | filters.CAPTION | filters.PHOTO | filters.Document.ALL,
        save_to_saved_messages
    ))
    application.run_polling()