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

porta_inicial_chat = 5000
porta_inicial_video = 5100
porta_inicial_audio = 5200
range_porta = 8

audio = pyaudio.PyAudio()

fps=0
st=0
frames_to_count=20
cnt=0

#definicoes para a interface
font = cv2.FONT_HERSHEY_DUPLEX 
font_scale = 0.5
font_color = (0, 30, 30)
text_offset_x = 20
text_offset_y = 600
chat_top = 620
chat_bottom = 800
messages_list = []

background = np.zeros((790, 700, 3), dtype=np.uint8)
background[:] = (240, 240, 240) 
cv2.putText(background, "Tarefa 1 - Sistemas Distribuidos", (70, 60), font, font_scale*1.4, font_color, 1, cv2.LINE_AA)
cv2.putText(background, "Chat de texto", (50, 580), font, font_scale, font_color, 1, cv2.LINE_AA)
cv2.rectangle(background, (10, 590), (780,780), (255,255,255), -1)



def publisher_chat(nome):
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)

    publisher.bind_to_random_port("tcp://*", min_port = porta_inicial_chat, max_port = porta_inicial_chat + range_porta, max_tries = range_porta) 

    while (True):
        message = input()
        message = f"[{nome}]: {message}"
        publisher.send_string(message)

def subscriber_chat():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    for porta in range(range_porta):
        subscriber.connect(f"tcp://localhost:{porta_inicial_chat + porta}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    while (True):
        global text_offset_y
        message = subscriber.recv_string()
        messages_list.append(message)
        
        background.fill(0)
        background[:] = (240, 240, 240) 
        cv2.putText(background, "Tarefa 1 - Sistemas Distribuidos", (70, 60), font, font_scale*1.4, font_color, 1, cv2.LINE_AA)
        cv2.putText(background, "Chat de texto", (50, 580), font, font_scale, font_color, 1, cv2.LINE_AA)
        cv2.rectangle(background, (10, 590), (780,780), (255,255,255), -1)
        
        if len(messages_list) * 30 > chat_bottom - chat_top:
             messages_list.pop(0)
             
        for i, message in enumerate(messages_list):
             y = chat_bottom - (len(messages_list) - i) * 30
             sender = message.split(":")[0]
             cor1 = (ord(sender[0])*5)%200
             cor2 = (ord(sender[1])*3)%200
             cor3 = (ord(sender[2])*7)%200
             
             cv2.putText(background, message, (text_offset_x, y), font, font_scale, (cor1, cor2, cor3), 1, cv2.LINE_AA)
             
        print(message)

def subscriber_video():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    for porta in range(range_porta):
        subscriber.connect(f"tcp://localhost:{porta_inicial_video + porta}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "")
    cv2.imshow("frame", background)
        
#aqui ------------------------------------------------------
    while (True):

		#imagem recebida
        raw_image = subscriber.recv()
        image = np.frombuffer(raw_image, dtype=np.uint8)
        frame = cv2.imdecode(image, 1)
        
		#interface bonitinha
        frame_height, frame_width, _ = frame.shape
        x_offset = (700 - frame_width) // 2
        y_offset = 70
        background[y_offset:y_offset+frame_height, x_offset:x_offset+frame_width] = frame
        
        
        cv2.imshow("frame", background)

        time.sleep(0.1)

        # detect any kepresses
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break

    cv2.destroyAllWindows()

     
def publisher_video(nome):
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)

    publisher.bind_to_random_port("tcp://*", min_port = porta_inicial_video, max_port = porta_inicial_video + range_porta, max_tries = range_porta) 

    vs = VideoStream(src=0, resolution=(640, 480)).start()
    time.sleep(2.0)  # allow camera sensor to warm up
    print(vs)

    while (True):
        frame = vs.read()
        encoded, buf = cv2.imencode('.jpg', frame)
        publisher.send(buf)
        #cv2.imshow(f"{nome}", frame)
        time.sleep(0.1)

        # detect any kepresses
        key = cv2.waitKey(1) & 0xFF

        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break
    
    cv2.destroyAllWindows()

def subscriber_audio():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)

    for porta in range(range_porta):
        subscriber.connect(f"tcp://localhost:{porta_inicial_audio + porta}")
        subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

    stream = audio.open(format=pyaudio.paInt16,channels=1,rate=44100,output=True)

    while (True):
        audio_data = subscriber.recv()
        stream.write(audio_data)

def publisher_audio(nome):
    context = zmq.Context()
    publisher = context.socket(zmq.PUB)

    publisher.bind_to_random_port("tcp://*",  min_port = porta_inicial_audio, max_port = porta_inicial_audio + range_porta, max_tries = range_porta) 
    
    stream = audio.open(format=pyaudio.paInt16,channels=1,rate=44100,input=True,frames_per_buffer=1024)

    while (True):
        audio_data = stream.read(1024)
        publisher.send(audio_data)

def main():
    nome = input("Digite o seu nome (min. 3 letras): ") 
    nome = nome.split(" ")

    subscriber_chat_thread = threading.Thread(target=subscriber_chat)
    subscriber_video_thread = threading.Thread(target=subscriber_video)
    subscriber_audio_thread = threading.Thread(target=subscriber_audio)

    publisher_chat_thread = threading.Thread(target=publisher_chat, args=(nome))
    publisher_video_thread = threading.Thread(target=publisher_video, args=(nome))
    publisher_audio_thread = threading.Thread(target=publisher_audio, args=(nome))

    subscriber_chat_thread.start()
    subscriber_video_thread.start()
    subscriber_audio_thread.start()

    publisher_chat_thread.start()
    publisher_video_thread.start()
    publisher_audio_thread.start()

    subscriber_chat_thread.join()
    publisher_chat_thread.join()
    subscriber_video_thread.join()
    publisher_video_thread.join()

    subscriber_audio_thread.join()
    publisher_audio_thread.join()

if __name__ == "__main__":
    main()