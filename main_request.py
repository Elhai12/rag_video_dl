from functions import response_request,import_index,setup_model,response_text

from fastapi import FastAPI,Request
from pydantic import BaseModel
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

app = FastAPI()

index = import_index()
chain = setup_model()
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

WEBHOOK_URL = f"https://rag-video-dl.onrender.com/{TELEGRAM_TOKEN}"


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


application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Ask question about deep learning")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_message = update.message.text
    try:

        response = get_answer(Question(question=user_message))
        model_response = response["response"]
    except Exception as e:
        model_response = f"error: {e}"

    await update.message.reply_text(model_response,parse_mode="Markdown")



application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))



@app.post(f"/{TELEGRAM_TOKEN}")
async def telegram_webhook(request: Request):

    try:
        update = Update.de_json(await request.json(), application.bot)
        application.process_update(update)
    except Exception as e:
        print(f"Error handling update: {e}")
    return {"status": "ok"}