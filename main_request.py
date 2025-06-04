from functions import response_request,import_index,setup_model

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
    return response_request(index,question.question,chain)
