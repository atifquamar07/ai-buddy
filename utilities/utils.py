"""
Author: Nishant Sharma (nishant@insituate.ai)

File: utilities/utils.py
Description: Implements various global methods for Nova
"""

from utilities.db_utils import *
from utilities.llm_utils import openai_response, bedrock_response, groq_response
from utilities.core_utils import remove_emojis, remove_prefixes, extract_quoted_content, get_uploaded_documents
import asyncio
import concurrent.futures
from google.cloud import texttospeech
import io
import zipfile
import json

async def generate_reply_1(user_utterance: str, user_name: str, conversation: str, user_id: str, db):
    buddy_preamble = load_text_file('utilities/prompts/buddy_preamble.txt').format(buddy_name=buddy_name, user_name=user_name)
    
    memory = get_memory(db=db, user_id=user_id)
    print(colored(f"Retrieved Memory: {memory}", 'red'))

    # To retrieve a summary
    user_summary = get_user_summary(user_id=user_id, db=db)

    # ------------------------------------------------------------------
    # Fetch any uploaded document content for additional context
    # ------------------------------------------------------------------
    documents_context = get_uploaded_documents(user_id=user_id)

    content = generate_final_prompt(user_id=user_id, user_name=user_name, memory=memory, user_utterance=user_utterance, conversation=conversation, buddy_name=buddy_name, user_summary=user_summary, doc_context=documents_context)
    prompt_list = [{"role": "system", "content": buddy_preamble}, {"role": "user", "content": content}]

    # Run reply and memory synthesis concurrently using asyncio.gather
    # This avoids the deadlock caused by running a new asyncio loop in a thread pool.
    reply_task = model_response(model_name=reply_model_name, prompt_list=prompt_list)
    memory_task = synthesize_memory(user_utterance=user_utterance, user_name=user_name, user_id=user_id, conversation=conversation, db=db)
    
    # Wait for both tasks to complete. We primarily need the reply.
    reply, _ = await asyncio.gather(reply_task, memory_task)

    return reply

async def synthesize_memory(user_utterance: str, user_name: str, user_id: str, conversation, db):
    if user_utterance != "":
        user_utterance = f"""The utterance is given by the user. Remember that you have to extract the memory from the utterance only.
        {user_utterance}
        """

    preamble = load_text_file('utilities/prompts/memory_preamble.txt')
    final_prompt = load_text_file('utilities/prompts/memory_prompt.txt').format(
        user_name=user_name,
        conversation=conversation,
        user_utterance=user_utterance
    )

    prompt_list = [{"role": "system", "content": preamble}, {"role": "user", "content": final_prompt}]

    response = await model_response(prompt_list=prompt_list, model_name=memory_model_name, structured='True-memory')
    
    if response['memory_found'] == True:
        update_memory(db=db, user_id=user_id, memory=response['memory'])
        return True
    else:
        return False

async def model_response(model_name: str, prompt_list: list, structured=False):
    global config

    if model_name == 'openai':
        reply = openai_response(prompt_list, structured=structured)
    elif model_name == 'bedrock':
        reply = bedrock_response(prompt_list, structured=structured)
    elif model_name == 'groq':
        reply = groq_response(prompt_list, structured=structured)
    else:
        reply = openai_response(prompt_list, structured=structured)

    # If the reply is a coroutine, await it
    if asyncio.iscoroutine(reply):
        reply = await reply

    # Remove emojis and prefixes from the reply
    reply = remove_prefixes(remove_emojis(reply), ['Nova:', 'Nova :', 'Haha,', 'haha,', 'nova:', 'nova: '])
    
    # New function to extract content within outermost quotes
    def extract_content(text):
        if text.startswith('"') and text.endswith('"'):
            return text[1:-1]
        return text

    return reply

async def generate_summary_and_insights(user_id: str, conversation: str, db: Session):
    # Load the summary prompt
    summary_prompt = load_text_file('utilities/prompts/summary_prompt.txt')
    print("limit 10")
    # Create the prompt list
    prompt_list = [
        {"role": "system", "content": "You are an AI assistant tasked with generating a summary of a user's conversation."},
        {"role": "user", "content": summary_prompt.format(conversation=conversation)}
    ]
    
    # Generate the summary using one of the models
    summary = await model_response(model_name=config['summary_model_name'], prompt_list=prompt_list, structured=False)
    
    # Add or update the summary in the database
    upsert_summary(user_id=user_id, summary=summary, db=db)
    
    return summary

def generate_text_to_speech(text: str):
    client = texttospeech.TextToSpeechClient.from_service_account_file('config/google_secret_key_tts.json')
    voice_type = config['tts_voice_google']
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE, name=voice_type
    )
    type = 'mp3'
    if 'Neural' in voice_type:
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        type = 'mp3'
    elif 'Journey' in voice_type:
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16
        )
        type = 'wav'

    input_text = texttospeech.SynthesisInput(text=text)
    response = client.synthesize_speech(
    input=input_text, voice=voice, audio_config=audio_config
    )
    return response, type

def prepare_combined_content(reply, speech, audio_type):
    audio_content = io.BytesIO(speech.audio_content)
    audio_content.seek(0)
    # Create a JSON response with the text reply
    json_response = json.dumps({"text": reply}).encode('utf-8')
    # Combine audio and JSON data
    combined_content = io.BytesIO()
    combined_content.write(json_response)
    combined_content.write(b'\n')  # Add a newline separator
    combined_content.write(audio_content.getvalue())
    combined_content.seek(0)
    return combined_content

def create_zip_stream(reply: str, speech, audio_type: str):
    """Return a BytesIO stream containing a ZIP archive with reply.json and the audio file."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('reply.json', json.dumps({"text": reply}))
        zip_file.writestr(f'audio.{audio_type}', speech.audio_content)
    zip_buffer.seek(0)
    return zip_buffer