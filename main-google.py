from flask import Flask, request, send_file
from utilities.utils import *
import os
from google.cloud import texttospeech

app = Flask(__name__)

conversation = ""

@app.route('/generate_audio', methods=['POST'])
def generate_audio():

    global conversation

    data = request.json
    user_input = data.get('utterance', '')
    user_name = data.get('user_name', 'Nishant')

    if user_input:
        reply = generate_reply_1(user_utterance=user_input, user_name=user_name, conversation=conversation)
        conversation += f"{user_name} : {user_input} \n"
        conversation += f"{buddy_name} : {reply}\n"
        #------------------TEST-----------------------
        conversation = ""
        #------------------TEST-----------------------


        # Google Text-to-Speech implementation
        client = texttospeech.TextToSpeechClient()

        input_text = texttospeech.SynthesisInput(text=reply)

        voice = texttospeech.VoiceSelectionParams(language_code="en-US")

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            effects_profile_id=["telephony-class-application"]
        )

        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )

        # Save the audio content to a file
        output_file_path = "output.mp3"
        with open(output_file_path, "wb") as out:
            out.write(response.audio_content)
            print(f'Audio content written to file "{output_file_path}"')

        # Stream the file back to the client
        return send_file(
            output_file_path,
            as_attachment=True,
            download_name="output.mp3",
            mimetype="audio/mpeg"
        )
    else:
        return {"error": "Invalid input"}, 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
