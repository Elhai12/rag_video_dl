import streamlit as st
from pinecone import Pinecone, ServerlessSpec, IndexEmbed, EmbedModel
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_core.output_parsers.string import StrOutputParser
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from langchain_mistralai import ChatMistralAI
from langchain_groq import ChatGroq
import json
from urllib.parse import urlparse, parse_qs
import re

@st.cache_resource
def import_index():
    key_pincone = st.secrets[""]

    index_name = "rag-video"
    pc = Pinecone(api_key=key_pincone)
    index = pc.Index(index_name)
    return index


def query_index(query, top_k=3):
    index = import_index()
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
def setup_model(model_selected):
    key_mistral = st.secrets[""]
    groq_key = st.secrets[""]
    llm = ChatMistralAI(
        model="devstral-small-2505",

        mistral_api_key= key_mistral
    )
    groq_model = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=groq_key

    )
    system_prompt = SystemMessagePromptTemplate.from_template(
        """
         Create quality summarize for the three provided transcript's clips.         
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
                "Summary: Based solely on transcripts the provided\n\n")
        ]
    )
    class answer(BaseModel):
        summary : str
    if model_selected == 'llama-3.1-8b':
        chain = prompt | groq_model | StrOutputParser()
    else:
        chain = prompt | llm.with_structured_output(answer)

    return chain


def gen_answer(model_selected,chunk1,chunk2,chunk3):
    chain = setup_model(model_selected)
    res = chain.invoke({"chunk1":chunk1,"chunk2":chunk2,"chunk3":chunk3})
    if model_selected == 'llama-3.1-8b':
        result = re.sub(r'(?:\*\*Summary(?: in \w+)?\*\*:|^.*?:)\s*(.*)', '', res)
    else:
        result = res.summary
    return result

def get_video_id(url):
  query = urlparse(url).query
  video_id = parse_qs(query).get('v', [None])[0]
  return video_id









