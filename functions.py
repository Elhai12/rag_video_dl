import streamlit as st
from langsmith import expect
from pinecone import Pinecone, ServerlessSpec, IndexEmbed, EmbedModel
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.output_parsers.string import StrOutputParser
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from langchain_mistralai import ChatMistralAI
from langchain_groq import ChatGroq
import json
from urllib.parse import urlparse, parse_qs
import os
from dotenv import load_dotenv




@st.cache_resource
def import_index():

    try:
        key_pincone = st.secrets.get("pincone")
    except Exception as e:
        if "streamlit" in str(e).lower():
            load_dotenv()
            key_pincone = os.getenv("pincone")


    index_name = "rag-video"
    pc = Pinecone(api_key=key_pincone)
    index = pc.Index(index_name)
    return index


def query_index(index,query, top_k=3):

    query_payload = {
        "inputs": {
            "text": query
        },
        "top_k": top_k
    }

    results = index.search(
        namespace="two_minutes_chunks",
        query= query_payload
    )
    results_data = []
    for match in results['result']['hits']:
        metadata = match['fields']['metadata']
        metadata = json.loads(metadata)
        score = match['_score']
        results_data.append({
            "url": metadata.get('url', ''),
            "title": metadata.get('title', ''),
            "text": match['fields'].get('chunk_text', ''),
            "start": metadata.get('start', ''),
            "end": metadata.get('end', ''),
            "score": score
        })
    return results_data

@st.cache_resource
def setup_model():
    try:
        key_mistral = st.secrets.get("mistral")
    except Exception as e:
        if "streamlit" in str(e).lower():
            load_dotenv()
            key_mistral = os.getenv("mistral")

    llm = ChatMistralAI(
        model="devstral-small-2505",

        mistral_api_key= key_mistral
    )

    system_prompt = SystemMessagePromptTemplate.from_template(
        """
        Analyze the following three clips transcripts in the context of a specific user question. Your tasks are as follows:
        
        Summarize how each clip addresses the question.
        
        Assign a relevance score (0-10) for each transcript based on how well it answers the question:
        
        0: Completely unrelated to the topic.
        
        10: Fully and comprehensively answers the question.
        
        If none of the transcripts are relevant, return a relevance score of 0 for all and explain why.
          
        """
    )

    prompt = ChatPromptTemplate(
        [
            system_prompt,
            HumanMessagePromptTemplate.from_template(
                "Question: {question}\n\n"
                "Provided transcripts:\n"
                "clip 1: {chunk1}\n"
                "clip 2: {chunk2}\n"
                "clip 3: {chunk3}\n\n"

               )
        ]
    )
    class answer(BaseModel):
        summary_clip1 : str
        score_clip1 : int
        summary_clip2: str
        score_clip2: int
        summary_clip3: str
        score_clip3: int

    chain = prompt | llm.with_structured_output(answer)

    return chain


def gen_answer(chain,question,chunk1,chunk2,chunk3):

    res = chain.invoke({"question":question,"chunk1":chunk1,"chunk2":chunk2,"chunk3":chunk3})
    result = []
    for clip in range(1, 4):
        sum = getattr(res, f"summary_clip{clip}")
        score = getattr(res, f"score_clip{clip}")
        result.append([sum, score])

    return result

def get_video_id(url):
  query = urlparse(url).query
  video_id = parse_qs(query).get('v', [None])[0]
  return video_id

def response_request(index,query,chain):
    all_results = query_index(index,query)
    texts = [t.get('text') for t in all_results]

    summary_results = gen_answer(chain,query,texts[0],texts[1],texts[2])
    return summary_results,all_results

def sec_hour_min(seconds,hour_minute):
    i=1
    if hour_minute == 'hour':
        i = 60
    hours_minutes = int(seconds//(60*i))
    rest = seconds%(60*i)
    rest_min_sec = int(rest/(1*i))
    return f"{hours_minutes}:{rest_min_sec}"



def response_text(summary_results, all_results):
    zip_results = zip(summary_results, all_results)
    text_res = ""
    for summary, video in zip_results:
        if summary[1]>=5:
            start_time = int(video['start'])
            url_fix = f"{video['url']}&start={start_time}"
            time_label = f"Minute {sec_hour_min(video['start'],'minute')}" if video['start'] <= 3600 else f"Hour {sec_hour_min(video['start'],'hour')}"
            text_res += f"📽️ **{video['title']}**  \n\n"
            text_res += f"{summary[0]}  \n\n"
            text_res += f"▶️ **Watch here from {time_label}: {url_fix}**\n\n"
    if text_res != "":
        return text_res
    else:
        return "**The question is not relevant to the deep learning topic.**"



