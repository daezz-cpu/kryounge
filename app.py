import streamlit as st
import pandas as pd
import numpy as np

st.title('My First Streamlit App')
st.write("Here's our first attempt at using data to create a table:")
st.write(pd.DataFrame({
    'first column':[1,2,3,4],
    'second column':[10,20,30,40]
}))

st.write("Streamlit supports a wide range of data visualizations, including [Plotly, Altair, and Bokeh charts](https://docs.streamlit.io/develop/api-reference/charts). 📊 And with over 20 input widgets, you can easily make your data interactive!")

all_users = ["Alice", "Bob", "Charly"]
with st.container(border=True):
    users = st.multiselect("Users", all_users, default=all_users)
    rolling_average = st.toggle("Rolling average")

np.random.seed(42)
data = pd.DataFrame(np.random.randn(20, len(users)), columns=users)
if rolling_average:
    data = data.rolling(7).mean().dropna()

tab1, tab2 = st.tabs(["Chart", "Dataframe"])
tab1.line_chart(data, height=250)
tab2.dataframe(data, height=250, use_container_width=True)

import streamlit as st
import random
import time

st.write("안녕, 오늘은 4학년이 되기 전 삶을 즐겁게 누릴 수 있는 방법을 알려줄게.")
st.caption("주영이의 임고 직전 행복한 하루보내기 작전")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"assistant", "content": "Let's start chatting!"}]
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role":"user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

with st.chat_message("assistant"):
    message_placeholder = st.empty()
    full_response = ""
    assistant_response = random.choice(
        [
            "오늘은 계획없이 버스를 타고 내리고 싶은 곳에서 내려보는 건 어때?",
            "맛있는 음식과 달달한 간식을 먹으며 따뜻한 저녁을 보내볼까?",
            "좋은 음악을 들으며 즐겨볼까?"
            "좋아하는 사람들을 만나며 이야기 나눌까?"
            "읽고 싶었던 책을 하루종일 읽어볼까?",
        ]
    )
    for chunk in assistant_response.split():
        full_response += chunk + " "
        time.sleep(0.05)
        message_placeholder.markdown(full_response + "|")
    message_placeholder.markdown(full_response)
st.session_state.messages.append({"role": "assistant", "content": full_response})
        
