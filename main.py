import streamlit as st
from streamlit_chat import message
from functions import query_index,gen_answer,get_video_id,import_index,setup_model,seconds_to_time_format


def is_hebrew(text):
    return any("\u0590" <= c <= "\u05FF" for c in text)

def dynamic_text(text, is_user=False):
    direction = "rtl" if is_hebrew(text) else "ltr"
    alignment = "right" if direction == "rtl" else "left"
    bubble_color = "#DCF8C6" if is_user else "#E1E1E1"
    text_color = "#000000"
    margin_side = "margin-left: auto;" if is_user else "margin-right: auto;"
    max_width = "70%"
    return f"""
    <div style="
        direction: {direction};
        text-align: {alignment};
        background-color: {bubble_color};
        color: {text_color};
        padding: 12px 16px;
        border-radius: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        {margin_side}
        max-width: {max_width};
        font-size: 16px;
        line-height: 1.4;
        margin-bottom: 10px;
        ">
        {text}
    </div>
    """

def clear_history():
    st.session_state.history = []

st.set_page_config(page_title="Smart Video RAG", page_icon="🤖", layout="wide")

index = import_index()
chain = setup_model()

col1, col2, col3 = st.columns([1,1,1])
with col1:
    # model_selected = st.radio(
    #     "Choose model:",
    #     ["devstral-small", "llama-3.1-8b"],
    #     label_visibility="visible",
    # )
    # st.markdown(f"<h1 style='font-size:14px;{model_selected}'></h1>",unsafe_allow_html=True)
    st.write("")
with col2:
    st.image("image3.png")
with col3:
    st.write("")

if "history" not in st.session_state:
    st.session_state.history = []
# if "count_res" not in st.session_state:
#     st.session_state.count_res = 0

def chat_with_bot(index,user_input,chain):
    transcripts = query_index(index,user_input)

    texts = [[f"Context: {c.get("text").split("\n")[0]}"] + [c.get("transcripts")] for c in transcripts]

    answer = gen_answer(chain,user_input,texts[0], texts[1], texts[2])
    videos = []
    for i,video in enumerate(transcripts):
        text = video.get('text')
        video_id = get_video_id(video.get("url"))
        #### start = int(video.get("start"))
        start = answer[i][2]
        url = f"https://www.youtube.com/embed/{video_id}?start={start}"
        videos.append({"title": video.get("title"), "url": url, "text": text,"start":start})
    return answer, texts, videos

def send_message():
    user_message = st.session_state.user_input.strip()
    if user_message:
        bot_response, relevant_docs, videos = chat_with_bot(index,user_message,chain)
        st.session_state.history.append({"user": user_message, "bot": bot_response, "videos": videos})
        st.session_state.user_input = ""



for i, msg in enumerate(st.session_state.history):

    count_res = 0
    st.markdown(dynamic_text(msg["user"], is_user=True), unsafe_allow_html=True)
    zip_ms_video = zip([ms for ms in msg["bot"]],[vid for vid in msg['videos']])
    zip_ms_video = sorted(zip_ms_video, key=lambda x: x[0][1], reverse=True)

    for ms,video in zip_ms_video:

        if ms[1]>=5:
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                st.write("")
            with col2:
                st.markdown(
                    f"""
                    <div>
                        <span style="font-size: 18px; font-weight: bold;">{video['title']}</span>
                        <br>
                        <span style="font-size: 14px; color: gray;">
                            Starts form: 
                      {seconds_to_time_format(video['start'])}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col3:
                st.write("")
            col1, col2,col3 = st.columns([2,3,1])
            with col1:
                st.markdown(dynamic_text(ms[0]+ f"\n\n<b>Relevance Score: {str(ms[1])}</b>", is_user=False), unsafe_allow_html=True)
                # st.markdown(dynamic_text(, is_user=False), unsafe_allow_html=True)
            with col2:
                st.markdown(
                    f"""
                    <iframe width="560" height="315" src="{video['url']}" 
                    frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                    """,

                    unsafe_allow_html=True,
                )
            with col3:
                with st.expander("Transcript",icon="📄"):
                    clean_transcript =  video['text'].split('\n', 1)[1]
                    st.write(clean_transcript)
            count_res+=1

    if count_res==0:
        st.markdown(dynamic_text("<b>The question is not relevant to the deep learning topic</b>", is_user=False), unsafe_allow_html=True)

with st.container():
    col1,col2 = st.columns([8,2])
    with col1:
        st.text_input("Type your message:",on_change= send_message,placeholder="Ask me something...",key="user_input",label_visibility="collapsed",)
    with col2:
        st.button("Send",on_click=send_message,icon=":material/send:")
    st.button("Clear Chat", on_click=clear_history)