# Grupo J
# Membros da equipe:
# Ana Carolina Castro Rosal - 769679
# Ana Ellen Deodato Perereira - 800206
# Gabriel Kusumota Nadalin - 819498
# João Victor Pacini - 769729

# Para executar o código, basta baixar as bibliotecas que estão no arquivo requirements.txt
# e usar o comando:
# "python chat_video_audio_local.py" para rodar o código.
# Para abrir novos usuários, basta abrir um novo terminal
# As portas já foram setadas no código para audio, video e texto.

"""Este código é uma versão final que envolve o tratamento de vídeo, 
a comunicação de rede usando o ZMQ e a interface gráfica com a biblioteca OpenCV. 
Ele inclui funções para publicar e assinar mensagens de chat, receber e enviar quadros de vídeo, 
receber e enviar áudio, bem como a função principal que gerencia as threads e a exibição da interface gráfica."""

#Requirements:
#cffi==1.15.1
#contourpy==1.1.0
#cycler==0.11.0
#fonttools==4.40.0
#importlib-resources==5.12.0
#imutils==0.5.4
#kiwisolver==1.4.4
#matplotlib==3.7.1
#numpy==1.24.3
#opencv-python==4.7.0.72
#packaging==23.1
#Pillow==9.5.0
#pycparser==2.21
#pyparsing==3.1.0
#pyshine==0.0.6
#python-dateutil==2.8.2
#pyzmq==25.1.0
#six==1.16.0
#sounddevice==0.4.6
#zipp==3.15.0
#zmq==0.0.0

import zmq
import threading
import cv2 as cv2
from imutils.video import VideoStream
import socket
import queue
import base64
import time
import numpy as np
import pyshine as ps
import pyaudio

# Configuração das portas iniciais e intervalo de portas para cada canal
porta_inicial_chat = 5000
porta_inicial_video = 5100
porta_inicial_audio = 5200
range_porta = 8

# Inicialização do objeto PyAudio para captura e reprodução de áudio
audio = pyaudio.PyAudio()

# Variáveis relacionadas ao processamento de vídeo
fps=0
st=0
frames_to_count=20
cnt=0

# Definições para a interface gráfica
font = cv2.FONT_HERSHEY_DUPLEX 
font_scale = 0.5
font_color = (0, 30, 30)
text_offset_x = 20
text_offset_y = 600
chat_top = 620
chat_bottom = 800
messages_list = []

# Criação do fundo da interface gráfica
background = np.zeros((790, 1210, 3), dtype=np.uint8)
background[:] = (240, 240, 240) 
cv2.putText(background, "Tarefa 1 - Sistemas Distribuidos", (70, 60), font, font_scale*1.4, font_color, 1, cv2.LINE_AA)
cv2.putText(background, "Chat de texto", (50, 580), font, font_scale, font_color, 1, cv2.LINE_AA)
cv2.rectangle(background, (10, 590), (780, 1200), (255,255,255), -1)

# Função para enviar mensagens de chat
def publisher_chat(nome):
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)

    # Vinculação a uma porta aleatória para enviar mensagens de chat
    publisher.bind_to_random_port("tcp://*", min_port=porta_inicial_chat, max_port=porta_inicial_chat + range_porta, max_tries=range_porta) 

    while True:
        message = input()
        message = f"{nome}: {message}"
        publisher.send_string(message)

# Função para receber mensagens de chat
def subscriber_chat():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    # Conexão aos canais de chat em todas as portas designadas
    for porta in range(range_porta):
        subscriber.connect(f"tcp://localhost:{porta_inicial_chat + porta}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    while True:
        global text_offset_y
        message = subscriber.recv_string()
        messages_list.append(message)
             
        print(message)

# Função para receber quadros de vídeo
def subscriber_video(frames_dict):
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    # Conexão aos canais de vídeo em todas as portas designadas
    for porta in range(range_porta):
        subscriber.connect(f"tcp://localhost:{porta_inicial_video + porta}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
    
    while True:
        participant_id = subscriber.recv_pyobj()
        raw_image = subscriber.recv()
        image = np.frombuffer(raw_image, dtype=np.uint8)
        frame = cv2.imdecode(image, 1)

        frames_dict[participant_id] = frame
        
def display_videonchat(frames_dict):
    background = np.zeros((790, 1210, 3), dtype=np.uint8)
    background[:] = (240, 240, 240)

    x_offsets = [10, 310, 610, 910, 10, 320, 610, 910]
    y_offsets = [70, 70, 70, 70, 300, 300, 300, 300]

    while True:
    
        background.fill(0)
        background[:] = (240, 240, 240) 
        cv2.putText(background, "Tarefa 1 - Sistemas Distribuidos", (70, 60), font, font_scale*1.4, font_color, 1, cv2.LINE_AA)
        cv2.putText(background, "Chat de texto", (50, 580), font, font_scale, font_color, 1, cv2.LINE_AA)
        cv2.rectangle(background, (10, 590), (1200,780), (255,255,255), -1)
        
        if len(messages_list) * 30 > chat_bottom - chat_top:
            messages_list.pop(0)
             
        for i, message in enumerate(messages_list):
            y = chat_bottom - (len(messages_list) - i) * 30
            sender = message.split(":")[0]
            cor1 = (ord(sender[0])*5) % 200
            cor2 = (ord(sender[1])*3) % 200
            cor3 = (ord(sender[2])*7) % 200
             
            cv2.putText(background, message, (text_offset_x, y), font, font_scale, (cor1, cor2, cor3), 1, cv2.LINE_AA)

	#desenha o video
        for i, participant_id in enumerate(frames_dict.keys()):
            if i < 8:
                frame = frames_dict[participant_id]
                frame = cv2.resize(frame, (300, 220))
                x_offset = x_offsets[i]
                y_offset = y_offsets[i]
                background[y_offset:y_offset+220, x_offset:x_offset+300] = frame
                cv2.putText(background, participant_id, (x_offset+20, y_offset+20), font, font_scale, (255,255,255), 1, cv2.LINE_AA)

        cv2.imshow("Video Frames", background)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            break

# Função para enviar quadros de vídeo
def publisher_video(nome):
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)

    # Vinculação a uma porta aleatória para enviar quadros de vídeo
    publisher.bind_to_random_port("tcp://*", min_port=porta_inicial_video, max_port=porta_inicial_video + range_porta, max_tries=range_porta) 

    vs = VideoStream(src=0, resolution=(640, 480)).start()
    time.sleep(2.0)

    while True:
        frame = vs.read()
        encoded, buf = cv2.imencode('.jpg', frame)
        publisher.send_pyobj(nome[0])
        publisher.send(buf)
        time.sleep(0.1)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

# Função para receber áudio
def subscriber_audio():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    for porta in range(range_porta):
        subscriber.connect(f"tcp://localhost:{porta_inicial_audio + porta}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, output=True)

    while True:
        audio_data = subscriber.recv()
        stream.write(audio_data)

# Função para enviar áudio
def publisher_audio(nome):
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)

    # Vinculação a uma porta aleatória para enviar áudio
    publisher.bind_to_random_port("tcp://*", min_port=porta_inicial_audio, max_port=porta_inicial_audio + range_porta, max_tries=range_porta) 
    
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)

    while True:
        audio_data = stream.read(1024)
        publisher.send(audio_data)

# Função principal
def main():
    nome = input("Digite o seu nome (mínimo 3 letras): ")
    nome = nome.split(" ")

    frames_dict = {}

    subscriber_chat_thread = threading.Thread(target=subscriber_chat)
    subscriber_video_thread = threading.Thread(target=subscriber_video, args=(frames_dict,))
    subscriber_audio_thread = threading.Thread(target=subscriber_audio)

    publisher_chat_thread = threading.Thread(target=publisher_chat, args=(nome,))
    publisher_video_thread = threading.Thread(target=publisher_video, args=(nome,))
    publisher_audio_thread = threading.Thread(target=publisher_audio, args=(nome,))

    subscriber_chat_thread.start()
    subscriber_video_thread.start()
    subscriber_audio_thread.start()

    publisher_chat_thread.start()
    publisher_video_thread.start()
    publisher_audio_thread.start()

    display_videonchat(frames_dict)

    subscriber_chat_thread.join()
    subscriber_video_thread.join()
    subscriber_audio_thread.join()

    publisher_chat_thread.join()
    publisher_video_thread.join()
    publisher_audio_thread.join()

if __name__ == "__main__":
    main()
