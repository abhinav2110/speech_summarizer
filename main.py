import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import asyncio
import openai

# Azure Speech and OpenAI configurations
speech_key = "45e443d2c8534039bf304cd4e63c0c34"
service_region = "eastus"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_recognition_language = "ar-SA"

openai.api_type = "azure"
openai.api_base = "https://df-pocs-q1.openai.azure.com/"
openai.api_version = "2024-02-01"
openai.api_key = "34a6e9e765d94d3c8a318337cbc122cd"

# Function to clean the response
def clean_response(response_text):
    cleaned_text = response_text.strip()
    return cleaned_text

# Function to summarize the recognized text using OpenAI
def summarize_text(text):
    prompt = f"""
    Summarize the following text by focusing ONLY on the core issues or specific actions mentioned. Ignore greetings, pleasantries, repetitive statements, irrelevant details, and any unimportant information.

    Text to summarize: {text}

    Instructions:

    Focus on the specific problems, requests, or actions described in the text.
    Omit greetings, repetitive content, and any irrelevant or filler information.
    Provide a concise summary that includes only the essential points.
    If no actionable or core issues are present, return an empty result.
    Use a concise numbered list (e.g., 1), 2), 3)).
    """
    try:
        response = openai.Completion.create(
            engine="gpt-35-turbo",
            prompt=prompt,
            max_tokens=200,
            temperature=0.3,
        )
        summary = response.choices[0].text.strip()
        return summary

    except Exception as e:
        return f"Error: {e}"

# Async function to recognize speech continuously
async def recognize_and_summarize(speech_recognizer, stop_word):
    done = False
    recognized_text = ""

    def recognized_cb(evt):
        nonlocal recognized_text, done
        recognized_text += evt.result.text + " "
    
        if stop_word.lower() in evt.result.text.lower():
            done = True
            speech_recognizer.stop_continuous_recognition()

    def session_stopped_cb(evt):
        nonlocal done
        done = True

    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.session_stopped.connect(session_stopped_cb)
    speech_recognizer.start_continuous_recognition()

    while not done:
        await asyncio.sleep(1)

    return recognized_text

# Streamlit UI
st.title("Speech to Text and Summarization App")

# Left column: for audio input options
with st.sidebar:
    st.subheader("Upload an audio file")
    audio_file = st.file_uploader("Drag and drop file here", type=["wav", "mp3"])

    use_microphone = st.button("Use Microphone")

# Initialize variables
recognized_text = ""
summary = ""

# Main logic for speech recognition and summarization
if audio_file is not None:
    # If an audio file is uploaded, process it
    audio_input = speechsdk.AudioConfig(filename=audio_file.name)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    stop_word = "stop"

    # Run the async speech recognition
    recognized_text = asyncio.run(recognize_and_summarize(speech_recognizer, stop_word))

    # Summarize the text using GPT
    summary = summarize_text(recognized_text)

elif use_microphone:
    # If microphone option is selected, use it for recognition
    audio_input = speechsdk.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    stop_word = "stop"

    # Run the async speech recognition
    recognized_text = asyncio.run(recognize_and_summarize(speech_recognizer, stop_word))

    # Summarize the text using GPT
    summary = summarize_text(recognized_text)

# Only show the text areas if text is available
if recognized_text:
    st.subheader("Transcribed Text")
    st.write(recognized_text)

if summary:
    st.subheader("Summary")
    st.write(summary)
