# ChatGPT + AWS

Last week **ChatGPT** was released and everyone has been trying amazing things. I also started playing with it and wanted to try how it would integrate using the **AI services** from **AWS** and the results are AWSome!

In this post I will explain step by step how I created this project so you can also do it:

https://dev.to/aws-builders/how-to-create-the-smartest-multilingual-virtual-assistant-using-aws-and-chatgpt-4i5k

Best of all, you don't need to be an **AI expert** to create this!

## Steps of the project

![Image description](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/zeg4425prh2v8c2ejt43.png)

I have devided this project in 8 steps:

1. Record an audio and save it in WAV format
2. Upload the audio file to Amazon S3
3. Transcribe and detect the language of the audio saved in S3 using Amazon Transcribe
4. Amazon Transcribe saves the transcript in Amazon S3
5. Send the transcription to ChatGPT
6. Receive the text answer from ChatGPT and remove code chunks
7. Convert the text to audio using the language detected in step 3 using Amazon Polly and download the audio in MP3 format
8. Reproduce the audio file

Before you start playing with it, you need to define the general parameters:

```{python}
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
```

Make sure that the user that you have created in AWS have access to Amazon S3, Amazon Transcribe and Amazon Polly.

I hope you enjoy it as much as I did when I was building and playing with these services. I think these state-of-the-art technologies have a lot of opportunities/potential and when we use all of them together the results are AWSome!

If you have any question, suggestion or comment please feel free to add them on the comments or contact me directly! :)
