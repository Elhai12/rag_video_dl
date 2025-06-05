from functions import response_request,import_index,setup_model,response_text

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

index = import_index()
chain = setup_model()


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
