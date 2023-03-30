import streamlit as st
import requests
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import AudioFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import openai
import os
import time
import datetime
import sys
import math
import pandas as pd
import numpy as np
import json

openai.organization = "org-s0nwmFpPMZ1GTwO7vxMm0B3T"
openai.api_key = "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"
openai.Model.list()

st.title('Meeting Summary App POC')

 # Get the current date
now = datetime.datetime.now()
encoding = "mp4"
endpoint = "https://api.openai.com/v1/audio/transcriptions"
# endpoint = "https://api.openai.com/v1/whisper"
file_pieces = []

def segment_file(output_file, directory):
    # Load the audio clip
    audio_clip = AudioFileClip(output_file)
    # Get the size of an MP3 file in bytes
    size_in_bytes = os.path.getsize(output_file)
    # Convert the size to megabytes
    size_in_mb = size_in_bytes / (1024 * 1024)
    # Get clip duration
    audio_length = audio_clip.duration
    # Calculate num of chunks clip needs to be split into
    num_chunks = math.ceil(size_in_mb / 25)
    segment_duration = audio_length // num_chunks
    file_pieces = []

    # Iterate over the segments and save each one as a separate file
    for i in range(num_chunks):
        # st.write("RANGE: ", i)

        if i == 0 or i == num_chunks-1:
            # Create one start and end time to cutout 
            if i == 0:
                start_time = segment_duration
                end_time = audio_length
            elif i == num_chunks - 1:
                start_time = 0
                end_time = audio_length - segment_duration

            segment_clip = audio_clip.cutout(start_time, end_time)  # THIS WORKS
            
        else:
            # Create two sets of start and end times to cutout
            # Calculate the start and end times of the segment
            start_time_a = 0
            end_time_a = i * segment_duration

            start_time_b = (i+1) * segment_duration
            end_time_b = audio_length

            segment_clip = audio_clip.cutout(start_time_a, end_time_a).cutout(start_time_b, end_time_b)  # THIS 
        
        # Create audio segment file name
        segment_file = directory + "/segment_" + str(i) + ".mp3"
        segment_filename = segment_file
        # st.write(segment_filename)
        segment_clip.write_audiofile(segment_filename)
        file_pieces.append(segment_filename)

    # Close the video clip
    audio_clip.close()
    
    return file_pieces

# uploaded_file = st.file_uploader("Choose a video or audio file")
uploaded_file = st.sidebar.file_uploader("Upload a recording of your meeting", type=["mp3", "mp4", "wav", "flac"])

# if uploaded_file is not None:
#     st.write(uploaded_file.type)

#     if uploaded_file.type == "video/mp4":
#         bytes_data = uploaded_file.read()  
#         file_name = uploaded_file.name.replace(".mp4", "")
#         directory = f"{now.year}/{now.month}/{now.day}/{file_name}"
#         if not os.path.isdir(directory):
#                 os.makedirs(directory)
#         output_file = f"{now.year}/{now.month}/{now.day}/{file_name}/{file_name}.mp4"

#         with open(output_file, 'wb') as out:
#             out.write(bytes_data)

#         st.write((uploaded_file))
#         st.write((uploaded_file.name.replace(".mp4", "")))

#         video_clip = VideoFileClip(output_file)
#         audio_file_name = directory + "/AudioExtract.mp3"
#         video_clip.audio.write_audiofile(audio_file_name)

#         audio_clip = AudioFileClip(audio_file_name)

#         reader = audio_clip.reader
#         # Get the audio file size in bytes from the audio reader info
#         size_in_bytes = reader.nbytes

#         # Convert the size to megabytes
#         size_in_mb = size_in_bytes / (1024 * 1024)
#         # size_in_bytes = audio_clip.filesize
#         # size_in_mb = size_in_bytes / (1024 * 1024)

#         if size_in_mb > 25:
#             st.write("Audio File is larger than 25MB, segmenting file for summary...")
#             file_pieces = segment_file(audio_file_name, directory)
#         else:
#             file_pieces.append(audio_file_name)


if st.sidebar.button('Summarize Video'):

    if uploaded_file is not None:
        # st.write(uploaded_file.type)

        if uploaded_file.type == "video/mp4":
            bytes_data = uploaded_file.read()  
            file_name = uploaded_file.name.replace(".mp4", "")
            directory = f"{now.year}/{now.month}/{now.day}/{file_name}"
            if not os.path.isdir(directory):
                    os.makedirs(directory)
            output_file = f"{now.year}/{now.month}/{now.day}/{file_name}/{file_name}.mp4"

            with open(output_file, 'wb') as out:
                out.write(bytes_data)

            st.sidebar.write((uploaded_file))
            # st.write((uploaded_file.name.replace(".mp4", "")))

            video_clip = VideoFileClip(output_file)
            audio_file_name = directory + "/AudioExtract.mp3"
            video_clip.audio.write_audiofile(audio_file_name)

            audio_clip = AudioFileClip(audio_file_name)

            reader = audio_clip.reader
            # Get the size of an MP3 file in bytes
            size_in_bytes = os.path.getsize(audio_file_name)

            # Convert the size to megabytes
            size_in_mb = size_in_bytes / (1024 * 1024)
           
            st.sidebar.write(round(size_in_mb, 1), "MB")

            if size_in_mb > 25:
                st.sidebar.write("Audio File is larger than 25MB, segmenting file for summary...")
                file_pieces = segment_file(audio_file_name, directory)
            else:
                file_pieces.append(audio_file_name)
            
        # Write the number of files created
        # st.write(len(file_pieces))

        # Write the file names
        st.sidebar.write(file_pieces)

        progress_bar = st.progress(0)
        for percent_complete in range(100):
            time.sleep(0.02)
            progress_bar.progress(percent_complete + 1)

        complete_transcript = ""
        complete_summary = ""

        for i in range(len(file_pieces)):

            input_file = open(file_pieces[i], 'rb')
            transcript = openai.Audio.transcribe("whisper-1", input_file)
            complete_transcript += transcript['text']

            if i == 0:
                prompt=f"From the Transcript below extract the speakers,\
                three main subjects and summarize the transcript in 5 main ideas. \
                Format each section of the response on separate lines\
                \Transcript: {transcript['text']}\n---\nSpeakers:\nSubjects:\nSummary:",
            else:
                prompt=f"From the Transcript below extract the speakers, \
                three main subjects and summarize the transcript in 5 main ideas. \
                Add the response to the current summary provided below as well, avoid duplicate information. \
                \nTranscript: {transcript['text']}\
                \n\nCurrent Summary: {complete_summary}"

            # Get a summary of the transcript using the OpenAI API
            response = openai.Completion.create(
                engine="text-davinci-003",
                # model="gpt-3.5-turbo",
                prompt = prompt,
                temperature=0.2,
                max_tokens=200,
                n = 1,
                stop=None,
                timeout=300,
            )
            summary = response.choices[0].text.strip()
            complete_summary = summary

        # Show the summary
        st.subheader("Summary")
        st.write(summary)

        # Display the transcript in the Streamlit app
        st.subheader("Transcript")
        st.download_button(
            "Download Transcript", complete_transcript
        )
        st.write(complete_transcript)