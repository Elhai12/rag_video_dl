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
        namespace="my-namespace",
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
         Create quality summarize for each part of th three provided transcript's clips.         
         'Do not use external knowledge or assumptions completely!'. 
         minimum 5 sentences 
        """
    )

    prompt = ChatPromptTemplate(
        [
            system_prompt,
            HumanMessagePromptTemplate.from_template(
                # "Question: {question}\n\n"
                "Provided transcripts:\n"
                "clip 1: {chunk1}\n"
                "clip 2: {chunk2}\n"
                "clip 3: {chunk3}\n\n"
               )
        ]
    )
    class answer(BaseModel):
        summary_clip1 : str
        summary_clip2: str
        summary_clip3: str

    chain = prompt | llm.with_structured_output(answer)

    return chain


def gen_answer(chain,chunk1,chunk2,chunk3):

    res = chain.invoke({"chunk1":chunk1,"chunk2":chunk2,"chunk3":chunk3})
    result = [res.summary_clip1,res.summary_clip2,res.summary_clip3]
    return result

def get_video_id(url):
  query = urlparse(url).query
  video_id = parse_qs(query).get('v', [None])[0]
  return video_id

def response_request(index,query,chain):
    all_results = query_index(index,query)
    texts = [t.get('text') for t in all_results]

    summary_results = gen_answer(chain,texts[0],texts[1],texts[2])
    return summary_results,all_results

def response_text(summary_results, all_results):
    zip_results = zip(summary_results, all_results)
    text_res = ""
    for summary, video in zip_results:
        start_time = int(video['start'])
        url_fix = f"{video['url']}&start={start_time}"
        time_label = f"Minute {round(video['start'] / 60, 2)}" if video['start'] <= 3600 else f"Hour {round(video['start'] / 3600, 2)}"
        text_res += f"📽️ **{video['title']}** \n"
        text_res += f"{summary} \n"
        text_res += f"▶️ Watch here from {time_label}: {url_fix}\n\n"

    return text_res



