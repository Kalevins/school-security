# USAR
# python client.py --server-ip "Direccion IP del servidor"

# Se importan los paquetes necesarios
from imutils.video import VideoStream
import imagezmq
import argparse
import socket
import time

# Se construye el analizador de argumentos
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--server-ip", required=True,
	help="ip address of the server to which the client will connect")
args = vars(ap.parse_args())

# Se Inicializa el objeto ImageSender con la dirección de socket del servidor
sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(
	args["server_ip"]))

# Se obtiene el hostname, se inicializa la transmisión de video y permitir que la camara inicie
rpiName = socket.gethostname()
vs = VideoStream(src=0).start()
time.sleep(2.0)
 
while True:
	# Lee el frame de la cámara y lo envía al servidor
	frame = vs.read()
	sender.send_image(rpiName, frame)