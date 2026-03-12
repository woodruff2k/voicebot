# ssh -T git@github.com
# streamlit run app.py --server.port 8080
from audiorecorder import audiorecorder
from dotenv import load_dotenv
from datetime import datetime
from openai import OpenAI
from gtts import gTTS
import streamlit as st
import numpy as np
# import openai
import base64
import io
import os


# openai.api_key = ""
load_dotenv()
client = OpenAI()


def STT(audio):
    filename = "input.mp3"
    wav_file = open(filename, "wb")
    # wav_file.write(audio.tobytes())
    wav_file.write(audio.export(io.BytesIO(), format="wav").getvalue())
    wav_file.close()

    audio_file = open(filename, "rb")
    # transcript = openai.Audio.transcribe("whisper-1", audio_file)
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    audio_file.close()
    os.remove(filename)
    # return transcript["text"]
    return transcript.text


def ask_gpt(prompt, model):
    # response = openai.ChatCompletion.create(model=model, messages=prompt)
    response = client.chat.completions.create(model=model, messages=prompt)
    # system_message = response["choice"][0]["message"]
    system_message = response.choices[0].message
    # return system_message["content"]
    return system_message.content


def TTS(response):
    # gTTS를 활용하여 음성 파일 생성
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    # 음원 파일 자동 재생
    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
        <audio autoplay="True">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True)
    os.remove(filename)


def main():
    # 기본 설정
    st.set_page_config(
        page_title="음성 비서 프로그램",
        layout="wide"
    )
    
    flag_start = False

    # session state 초기화
    if "chat" not in st.session_state:
        st.session_state["chat"] = []
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "system", 
                "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korean"
            }
        ]
    if "check_audio" not in st.session_state:
        st.session_state["check_audio"] = []

    st.header("음성 비서 프로그램")
    st.markdown("---")

    # 기본 설명 영역
    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write(
            """
            - 음성 비서 프로그램의 UI는 스트림릿을 활용했습니다.
            - STT(Speech-To-Text)는 OpenAI의 Whisper AI를 활용했습니다.
            - 답변은 OpenAI의 GPT 모델을 활용했습니다.
            - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용했습니다.
            """
        )
        st.markdown("")

    # 옵션 선택 영역
    with st.sidebar:
        # openai.api_key = st.text_input(label="OPENAI API 키", placeholder="Enter Your API Key", value="", type="password")
        st.markdown("---")
        model = st.radio(label="GPT 모델", options=["gpt-5-mini", "gpt-3.5-turbo"])
        st.markdown("---")
        if st.button(label="초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [
                {
                    "role": "system", 
                    "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korean"
                }
            ]

    # 기능 구현 영역
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("질문하기")
        # !brew install ffmpeg
        audio = audiorecorder("클릭하여 녹음하기", "녹음 중 - 클릭하여 중단")
        # 녹음을 실행하면?
        if len(audio) > 0 and not np.array_equal(audio, st.session_state["check_audio"]):
            # 음성 재생
            # st.audio(audio.tobytes())
            st.audio(audio.export(io.BytesIO(), format="wav").getvalue())
            # 음원 파일에서 텍스트 추출
            question = STT(audio)

            # 채팅을 시각화하기 위해 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("user", now, question)]

            # 질문 내용 저장 (for ChatGPT API)
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "user", "content": question}]
            st.session_state["check_audio"] = audio
            flag_start = True

    with col2:
        st.subheader("질문/답변")
        if flag_start:
            response = ask_gpt(st.session_state["messages"], model)
            # 채팅 시각화를 위한 답변 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]
            st.session_state["messages"] = st.session_state["messages"] + [{"role": "user", "content": response}]

            # 채팅 형식으로 시각화하기
            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    st.write("")

            # gTTS를 활용하여 음성 파일 생성 및 재생
            TTS(response)
                

if __name__ == "__main__":
    main()
