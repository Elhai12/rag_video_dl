from functions import response_request,import_index,setup_model,response_text

from fastapi import FastAPI,Request
from pydantic import BaseModel
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import httpx
import asyncio
from telegram.constants import ParseMode

app = FastAPI()

index = import_index()
chain = setup_model()
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
app_url = os.getenv("URL")
WEBHOOK_URL = f"{app_url}/{TELEGRAM_TOKEN}"


class Question(BaseModel):
    question: str

# API endpoint
@app.post("/ask")
def get_answer(question: Question):
    summaries,videos = response_request(index,question.question,chain)
    response_text_all = response_text(summaries, videos)
    return {
        "response": response_text_all,
        "format": "markdown"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Ask question about deep learning")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text


    try:
        await update.message.reply_text("_Processing…_", parse_mode="Markdown")
    except Exception:
        pass


    try:
        loop = asyncio.get_event_loop()
        answer = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                get_answer,
                Question(question=user_message)
            ),
            timeout=45.0
        )
        model_response = answer["response"]
    except asyncio.TimeoutError:
        model_response = "The model not response in the time."
    except Exception as e:
        model_response = f"error: {e}"


    try:
        await update.message.reply_text(model_response, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Error sending reply to Telegram: {e}")





application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))



@app.post(f"/{TELEGRAM_TOKEN}")
async def telegram_webhook(request: Request):

    try:
        update = Update.de_json(await request.json(), application.bot)
        await application.process_update(update)
    except Exception as e:
        print(f"Error handling update: {e}")
    return {"status": "ok"}

async def ping_loop():

    if not app_url:
        print("APP_URL not define")
        return

    async with httpx.AsyncClient() as client:
        while True:
            try:
                ping_url = f"{app_url}/health"
                resp = await client.get(ping_url, timeout=10.0)
                print(f"[Ping] GET {ping_url} → {resp.status_code}")
            except Exception as e:
                print(f"[Ping Error] {e}")
            await asyncio.sleep(600)

@app.on_event("startup")

async def on_startup():


    try:
        await application.initialize()
        await application.start()
        print("Telegram Application initialized and started.")
    except Exception as e:
        print(f"Error initializing/starting Telegram application: {e}")


    try:
        was_set = await application.bot.set_webhook(WEBHOOK_URL)
        if was_set:
            print(f"✅ Webhook set successfully to: {WEBHOOK_URL}")
        else:
            print(f"❌ Failed to set webhook to: {WEBHOOK_URL}")
    except Exception as e:
        print(f"Error setting webhook: {e}")


    asyncio.create_task(ping_loop())
    print("🕰️ Ping loop task created (every 10 minutes).")

