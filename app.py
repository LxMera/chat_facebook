from flask import Flask, request
import requests
from openai import OpenAI
import os

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

client = OpenAI(api_key=os.environ.get('OPENAI_KEY'))
assistant_id = os.environ.get('ASSISTANT_ID')
thread = client.beta.threads.create()

def bot_ventas(input_text):
    try:
        client.beta.threads.messages.create(thread_id=thread.id,
                                            role="user",
                                            content=input_text)
         
        run = client.beta.threads.runs.create(thread_id=thread.id,
                                              assistant_id=assistant_id)
        while run.status!='completed':
            run = client.beta.threads.runs.retrieve(thread_id=thread.id,
                                                    run_id=run.id)            
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response = messages.data[0].content[0].text.value        
        return response
    except Exception as exc:
        return str(exc)

@app.route('/webhook', methods=['GET'])
def verify():
    # Facebook enviará una solicitud GET a este endpoint con un 'hub.challenge' y un 'hub.verify_token'.
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if not request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return 'Verification token mismatch', 403
        return request.args['hub.challenge'], 200
    return 'Hello world', 200


@app.route('/webhook', methods=['POST'])
def webhook():
    # Punto donde se reciben los mensajes
    data = request.get_json()
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                sender_id = messaging_event['sender']['id']  
                recipient_id = messaging_event['recipient']['id']  

                if messaging_event.get('message'):  
                    message_text = messaging_event['message']['text'] 
                    response = bot_ventas(message_text)  
                    send_message(sender_id, response)  

    return 'OK', 200

@app.route('/favicon.ico')
def favicon():
    return ('', 204)

def send_message(recipient_id, message_text):
    # Función para enviar el mensaje de respuesta
    params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    }
    response = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, json=data)
    if response.status_code != 200:
        print(response.status_code)
        print(response.text)

if __name__ == '__main__':
    app.run(debug=True)