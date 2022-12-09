# Import all libraries at the beginning
import uuid
import time
import boto3
import re
import os
import IPython.display as ipd
import sounddevice as sd
import soundfile as sf
import librosa
from revChatGPT.revChatGPT import Chatbot
import urllib.request
import json
from IPython.display import Audio
from IPython.display import display
import subprocess

#-- Define params --

# ChatGPT params
chatGPT_session_token = "<SESSION-TOKEN>"

# AWS params
aws_access_key_id = "<ACCESS-KEY-ID>"
aws_secret_access_key = "<SECRET-ACCESS-KEY>"
aws_default_region = "<AWS-REGION>"
aws_default_s3_bucket = "<S3-BUCKET>"

# Voice recording params
samplerate = 48000
duration = 4 #seconds

#-- Record audio and save it in WAV format --

def record_audio(duration, filename):
    print("[INFO] Start of the recording")
    mydata = sd.rec(int(samplerate * duration), samplerate=samplerate,channels=1, blocking=True)
    print("[INFO] End of the recording")
    sd.wait()
    sf.write(filename, mydata, samplerate)
    print(f"[INFO] Recording saved on: {filename}")

#Check if folder "audios" exists in current directory, if not then create it
if not os.path.exists("audio"):
    os.makedirs("audio")

# Create a unique file name using UUID
filename = f'audio/{uuid.uuid4()}.wav'

record_audio(duration, filename)

#-- Upload audio file to Amazon S3 --

# Connect to Amazon S3 using Boto3
def get_s3_client():
    return(boto3.client('s3', region_name=aws_default_region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key))

def upload_file_to_s3(filename):
    s3_client = get_s3_client()
    try:
        with open(filename, "rb") as f: 
            s3_client.upload_fileobj(f, aws_default_s3_bucket, filename)
            print(f"[INFO] File has been uploaded successfully in the S3 bucket: '{aws_default_s3_bucket}'")
    except:
        raise ValueError(f"[ERROR] Error while uploading the file in the S3 bucket: '{aws_default_s3_bucket}'")

upload_file_to_s3(filename)

#-- Convert Audio to Text using Amazon Transcribe --

# Generate UUID for the job id
job_id = str(uuid.uuid4())

# Connect to Amazon Transcribe using Boto3
def get_transcribe_client():
    return(boto3.client('transcribe', region_name=aws_default_region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key))

def get_text_from_audi(filename):
    transcribe = get_transcribe_client()
    print("[INFO] Starting transcription of the audio to text")
    transcribe.start_transcription_job(TranscriptionJobName=job_id, Media={'MediaFileUri': f"https://{aws_default_s3_bucket}.s3.{aws_default_region}.amazonaws.com/{filename}"}, MediaFormat='wav', IdentifyLanguage=True)
    print("[INFO] Transcribing text: *",end="")
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_id)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        print("*",end='')
        time.sleep(2)
    print("") #End of line after loading bar
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        response = urllib.request.urlopen(status['TranscriptionJob']['Transcript']['TranscriptFileUri'])
        data = json.loads(response.read())
        language_detected = data['results']['language_identification'][0]['code']
        transcript = data['results']['transcripts'][0]['transcript']
        print(f"[INFO] Transcription completed!")
        print(f"[INFO] Transcript language: {language_detected}")
        print(f"[INFO] Transcript text: {transcript}")
        return(transcript, language_detected)
    else:
        raise ValueError("[ERROR] The process to convert audio to text using Amazon Transcribe has failed.")

transcript, language_detected = get_text_from_audi(filename)

#-- Send Text to ChatGPT and get the answer --
def get_gpt_answer(prompt):
    print(f"[INFO] Sending transcript to ChatGPT")
    config = {"email": "<API-KEY>","session_token": chatGPT_session_token}
    chatbot = Chatbot(config, conversation_id=None)
    chatbot.refresh_session()
    response = chatbot.get_chat_response(prompt, output="text")["message"]
    print(f"[INFO] ChatGPT answer: {response}")
    return(response)

chatgpt_answer = get_gpt_answer(transcript)

#-- Convert Text to Audio using Amazon Polly --

def get_polly_client():
    return boto3.client('polly', region_name=aws_default_region, endpoint_url=f"https://polly.{aws_default_region}.amazonaws.com", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

def generate_audio(polly, text, output_file, voice, format='mp3'):
    text = clean_audio_text(text)
    resp = polly.synthesize_speech(Engine='neural', OutputFormat=format, Text=text, VoiceId=voice)
    soundfile = open(output_file, 'wb')
    soundBytes = resp['AudioStream'].read()
    soundfile.write(soundBytes)
    soundfile.close()
    print(f"[INFO] Response audio saved in: {output_file}")

def clean_audio_text(text):
    # Clean the code chuncks from the audio using regex
    result = re.sub(r"```[^\S\r\n]*[a-z]*\n.*?\n```", '', text, 0, re.DOTALL)
    return(result)

def speak_notebook(output_file):
    print(f"[INFO] Start reproducing response audio")
    display(Audio(output_file, autoplay=True))

def speak_script(output_file):
    print(f"[INFO] Start reproducing response audio")
    return_code = subprocess.call(["afplay", output_file])

def get_speaker(language_detected):
    # Get speaker based on the language detected by Amazon Transcribe (more info about available voices: https://docs.aws.amazon.com/polly/latest/dg/voicelist.html)
    voice = ""
    if language_detected == "en-US":
        voice = "Joanna"
    elif language_detected == "en-GB":
        voice = "Amy"
    elif language_detected == "en-IN":
        voice = "Kajal"
    elif language_detected == "ca-ES":
        voice = "Arlet"
    elif language_detected == "es-ES":
        voice = "Lucia"
    elif language_detected == "es-MX":
        voice = "Mia"
    elif language_detected == "es-US":
        voice = "Lupe"
    else:
        voice = "Joanna"
        print(f"[WARNING] The language detected {language_detected} is not supported on this code. In this case the default voice is Joanna (en-US).")
    print(f"[INFO] Speaker selected: {voice}")
    return(voice)

polly = get_polly_client()
voice = get_speaker(language_detected)
output_file = f"audio/{job_id}.mp3"
generate_audio(polly, chatgpt_answer, output_file,voice=voice)
speak_script(output_file)
