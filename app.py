from flask import Flask, render_template, request, send_file, redirect, url_for
import base64
import re
import pandas as pd
import os
import wave
import requests
import qrcode
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from fpdf import FPDF

app = Flask(__name__)

# Function to record audio and save it as a WAV file
def save_audio(audio_data):
    with open("output.wav", "wb") as f:
        f.write(audio_data)

# Function to convert audio file to base64 string
def convert_audio_to_base64(audio_data):
    
    base64_data = base64.b64encode(audio_data)
    base64_string = base64_data.decode('utf-8')
    
    return base64_string

# Function to extract text from API response
def extract_text_from_response(response):
    if response is not None and response.status_code == 200:
        response_json = response.json()
        if 'data' in response_json and 'source' in response_json['data']:
            return response_json['data']['source']
    return "Error: Unable to extract text from response"

# Function to convert textual numbers to numerical format
def convert_text_to_numbers(text):
    # # Process the text with spaCy
    # doc = nlp(text)
    # print(doc)
    text = text.lower()
    words = text.strip().split()
    # Initialize variables to store the numerical value
    sent = []
    nums = []
    numerical_value = 0
    current_number = 0  # Tracks the current number being formed
    multiplier = 1  # Multiplier for tens, hundreds, etc.

    # Define a mapping of words to numerical values
    word_to_num = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
        'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19,
        'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
        'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
        'hundred': 100, 'thousand': 1000, 'lakh': 100000, 'crore': 10000000
    }
  
    for i, word in enumerate(words):
        # Check if the word is a number word
        # print(word,current_number,numerical_value)
        if word in word_to_num and word not in ['hundred', 'thousand', 'lakh', 'crore']:
            numerical_value += word_to_num[word]
            current_number = word_to_num[word]
        # Check if the word is a multiplier
        elif word in ['hundred', 'thousand', 'lakh', 'crore']:
            # print("executed")
            multiplier = word_to_num[word]
            # Check if the previous word is a number
            # print(words[i-1])
            # if i > 0 and words[i - 1] in list(word_to_num.keys()):
            #     prev = current_number
            #     current_number -= word_to_num[words[i - 1]]
            #     print(prev,current_number)
            
            numerical_value -= current_number
            numerical_value += current_number * multiplier
            if multiplier > 100:
                current_number = 0  # Reset the current number
        # Ignore other tokens
        else:
            if word=='and' and i-1>=0 and i+1<len(words) and words[i-1] in word_to_num and words[i+1] in word_to_num:
                pass
            else:
                sent.append(word)
                
        if i+1<len(words) and words[i+1] not in word_to_num and words[i+1]!='and' and word in word_to_num:
            nums.append(numerical_value)
            sent.append(str(numerical_value))
            numerical_value = 0

    # Add the last formed number
    # numerical_value += current_number
    print(sent)
    return ' '.join(sent),numerical_value 

# Function to transcribe audio using an API
def translate_text(audio_file):
    # Your transcription API logic here
    audio_base64 = convert_audio_to_base64(audio_file)
    # Use the base64 string in your API request
    bhashini_api = "https://meity-auth.ulcacontrib.org/ulca/apis/asr/v1/model/compute"
    bhashini_input = {
        "modelId": "64117455b1463435d2fbaec4",
        "task": "asr",
        "audioContent": audio_base64,
        "source": "hi",
        "userId": "eb2d99d0aad045d693a6f0347d46599e"
    }
    
    # Test the ASR API with the base64-encoded audio data
    response = requests.post(bhashini_api, json=bhashini_input)
    print(f'transcript - {response.json()}' )
    
    if response.status_code == 200:
        # Extract the text from the response
        source_text = extract_text_from_response(response)
        
        print(f'source text - {source_text}')
        
        # Use the extracted text in the translation API request
        translation_api = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/compute"
        translation_input = {
            "modelId": "641d1cd18ecee6735a1b372a",
            "task": "translation",
            "input": [{"source": source_text}],
            "userId": "eb2d99d0aad045d693a6f0347d46599e"
        }
        
        # Send the translation API request
        translation_response = requests.post(translation_api, json=translation_input)
        
        # print(f'translation reposnse {translation_response}')
        
        if translation_response.status_code == 200:
            print("Translation:")
            print(translation_response.json())
            
            # Extract translated text from response
            translated_text = translation_response.json()['output'][0]['target']
            
            # Convert textual numbers to numerical format
            sentence, numbers = convert_text_to_numbers(translated_text)
            print("Sentence:")
            print(sentence)
            # print("Numbers used:")
            # print(numbers)
        else:
            print("Translation request failed.")
    else:
        print("ASR request failed.")
    
    return sentence


def calculate_sum(sentence):
    words = sentence.strip().split()
    curr_num = -1
    sent = []
    numbers_used = []
    i=0
    while i<len(words) :
        if words[i].isdigit():
            if curr_num==-1:
                if (i+2<len(words) and words[i+1]=='and' and words[i+2].isdigit()) or (i+1<len(words) and words[i+1].isdigit()):
                    curr_num+=int(words[i])
                else:
                    sent.append(words[i])
            else:
                if words[i-1].isdigit():
                    curr_num*=int(words[i])
                elif words[i-1]=='and':
                    curr_num+=int(words[i])
                    sent.append(str(curr_num))
                    numbers_used.append(curr_num)
                    curr_num=-1            
        else:
            if words[i]=='and' and words[i-1].isdigit() and i+1<len(words) and words[i+1].isdigit():
                pass
            else:
                sent.append(words[i])
        i+=1
    new_sentence = ' '.join(sent)   
    print(sent)   
    return new_sentence, numbers_used  

bill = []

def calculate_total_cost(sentence, prices):
    bill = []
    total_cost = 0
    quantity = 0
    # Find numbers and product names in the sentence
    for word in re.findall(r"[\w]+", sentence):
        if word.isdigit():
            quantity = int(word)
        elif len(word) < 4:
            # Search directly for words with length less than 4
            if word in prices:
                print(word,quantity)
                total_cost += prices[word] * quantity
                bill.append((word,quantity,prices[word],prices[word] * quantity))
                quantity = 0  # Reset quantity after processing
        else:
            # Search for words with length 4 or more based on the first 4 letters
            for key, value in prices.items():
                if key[:4] == word[:4]:
                    if quantity!=0:
                        print(key,quantity)
                        total_cost += value * quantity
                        bill.append((key,quantity,value,value*quantity))
                    else:
                        print(key,quantity+1)
                        total_cost += value
                        bill.append((key,quantity+1,value,value))
                    quantity = 0  # Reset quantity after processing
                    break

    return bill,total_cost


# Function to generate and download bill PDF
def generate_bill(sentence):
    # Your bill generation logic here
    prices = {
        "potato": 20,
        "onion": 25,
        "tomato": 30,
        "carrot": 40,
        "capsicum": 60,
        "cabbage": 35,
        "cauliflower": 45,
        "beetroot": 50,
        "brinjal": 25,
        "spinach": 15,
        "bitter-gourd": 55,
        "bottle-gourd": 30,
        "ridge-gourd": 40,
        "green-chili": 80,
        "coriander": 10,
        "mint": 12,
        "ladyfinger": 45,
        "cucumber": 20,
        "garlic": 70,
        "ginger": 90,
        "apple": 80,
        "banana": 35,
        "mango": 60,
        "grapes": 100,
        "orange": 40,
        "pomegranate": 70,
        "watermelon": 20,
        "kiwi": 90,
        "pineapple": 50,
        "strawberry": 120,
        "milk": 60,
        "curd": 50,
        "butter": 250,
        "cheese": 400,
        "paneer": 200,
        "rice": 50,
        "wheat": 30,
        "flour": 30,
        "sugar": 45,
        "salt": 20,
        "tea-leaves": 250,
        "coffee-powder": 300,
        "turmeric-powder": 40,
        "cumin-seeds": 120,
        "mustard-seeds": 80,
        "black-pepper": 150,
        "garam-masala": 200,
        "cinnamon-sticks": 180,
        "cloves": 250,
        "cardamom": 350,
        "chana-dal": 80,
        "moong-dal": 70,
        "urad-dal": 90,
        "masoor-dal": 60,
        "toor-dal": 100,
        "gram-flour": 60,
        "notebook": 50,
        "pen": 10,
        "pencil": 5,
        "eraser": 3,
        "ruler": 8,
        "sharpener": 4,
        "scissors": 30,
        "glue-stick": 20,
        "highlighter": 15,
        "marker": 25,
        "color-pencils": 40,
        "ballpoint-pen": 12,
        "stapler": 50,
        "paper-clips": 6,
        "tape": 15,
        "note-pad": 25,
        "whiteboard-marker": 30,
        "folder": 20,
        "calculator": 150,
        "calendar": 100
    }
    
    bill,total_cost = calculate_total_cost(sentence, prices)
    print("Total cost:", total_cost, "Indian Rupees")
    print(bill)
    
    # Initialize PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Use a font that supports Unicode characters
    # pdf.add_font("DejaVuSans", fname="fonts/DejaVuSans.ttf", uni=True)
    # pdf.set_font("DejaVuSans", size=12)

    # Add title
    pdf.cell(200, 10, txt="Bill", ln=True, align="C")

    # Add headers
    pdf.cell(40, 10, "Item", 1, 0, "C")
    pdf.cell(40, 10, "Quantity", 1, 0, "C")
    pdf.cell(40, 10, "Rate", 1, 0, "C")
    pdf.cell(40, 10, "Cost", 1, 1, "C")

    # Add bill items
    for item in bill:
        pdf.cell(40, 10, str(item[0]), 1, 0, "C")
        pdf.cell(40, 10, str(item[1]), 1, 0, "C")
        pdf.cell(40, 10, str(item[2]), 1, 0, "C")
        pdf.cell(40, 10, str(item[3]), 1, 1, "C")

    # Add total cost
    pdf.cell(160, 10, "Total cost", 1, 0, "R")
    pdf.cell(40, 10, f"Rs.{total_cost}", 1, 1, "C")

    print("before PDF downloaded")

    # Save the PDF to a temporary file
    pdf_filename = "bill.pdf"
    pdf.output(f'static/{pdf_filename}')

    # Serve the PDF file
    send_file(f'static/{pdf_filename}', mimetype='application/pdf', as_attachment=True)
    print("PDF downloaded")
    return total_cost, pdf_filename

upi_id="7488820018hhhg@ybl"
def generate_qr(amount, upi_id, filename):
    # Format the payment URL for UPI payment
    payment_url = f"upi://pay?pa={upi_id}&pn=Recipient&am={amount}&cu=INR"
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add payment URL to QR code
    qr.add_data(payment_url)
    qr.make(fit=True)
    
    # Create an image from the QR code
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save the image to a file
    filename = 'qr_code.png'
    qr_img.save(f'static/{filename}')
    send_file(f'static/{filename}', as_attachment=True)
    print(f"QR code for payment of {amount} INR to UPI ID {upi_id} generated!")
    return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record')
def record():
    return render_template('record.html')

@app.route('/process_audio', methods=['GET','POST'])
def process_audio():
    
    
    if request.method == 'POST':
        audio_data = request.files['audio'].read()
    print('Audio data: ',audio_data)
    save_audio(audio_data)
    translated_text = translate_text(audio_data)
    total_cost,bill_pdf = generate_bill(translated_text)
    qr_code = generate_qr(total_cost, "8306097026@apl",bill_pdf)  # Example: total_cost and UPI ID
    print('Audio Processed successfully!')
    bill = []
    return redirect(url_for('qr_page'))

@app.route('/qr_page')
def qr_page():
    return render_template('qr_page.html')

@app.route('/download-bill')
def download_bill():
    return send_file('bill.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)