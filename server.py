# USAR
# sudo python server.py --prototxt MobileNetSSD_deploy.prototxt --model MobileNetSSD_deploy.caffemodel --montageW 2 --montageH 2

# Se importan los paquetes necesarios
from imutils import build_montages
from datetime import datetime
import numpy as np
import imagezmq
import argparse
import imutils
import cv2
import time
import pickle
import os.path
import io
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
import subprocess

# Se construye el analizador de argumentos
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--prototxt", required=True,
	help="path to Caffe 'deploy' prototxt file")
ap.add_argument("-m", "--model", required=True,
	help="path to Caffe pre-trained model")
ap.add_argument("-c", "--confidence", type=float, default=0.2,
	help="minimum probability to filter weak detections")
ap.add_argument("-mW", "--montageW", required=True, type=int,
	help="montage frame width")
ap.add_argument("-mH", "--montageH", required=True, type=int,
	help="montage frame height")
args = vars(ap.parse_args())

# Se inicializa el objeto ImageHub
imageHub = imagezmq.ImageHub()

# Se inicializa la lista de etiquetas de clase MobileNet SSD que fueron entrenadas para
# detectar, luego se genera un conjunto de cuadros delimitadores de diferente color para cada clase
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
	"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
	"sofa", "train", "tvmonitor"]

# Se carga el modelo serializado desde el disco
print("[INFO] Cargando Modelo...")
net = cv2.dnn.readNetFromCaffe(args["prototxt"], args["model"])

# Se inicializa el conjunto de consideraciones (etiquetas de clase que nos interesan y queremos 
# contar), ademas del diccionario de recuento de objetos y el diccionario de frames
CONSIDER = set(["person"])
objCount = {obj: 0 for obj in CONSIDER}
frameDict = {}

# Se inicializa el diccionario que contendrá la información sobre cuándo un dispositivo estuvo 
# activo por última vez, luego se almacena la última vez que se realizó la comprobación (Ahora)
lastActive = {}
lastActiveCheck = datetime.now()

# Se almacena el número estimado de Pis, el período de verificación se activa, y se calcula la duración 
# en segundos a esperar antes de hacer una verificación para ver si un dispositivo estaba activo
ESTIMATED_NUM_PIS = 4
ACTIVE_CHECK_PERIOD = 10
ACTIVE_CHECK_SECONDS = ESTIMATED_NUM_PIS * ACTIVE_CHECK_PERIOD

# Se asigna el ancho y alto del montaje para que se puedan ver todos los frames entrantes en un 
# solo "dashboard"
mW = args["montageW"]
mH = args["montageH"]
print("[INFO] Detectando: {}...".format(", ".join(obj for obj in
	CONSIDER)))

# Se inicializan variables de control para el manejo de la API 
contador = 0
tiempo_inicial = time.time()
# Guarda los id, de las imagenes que se suben, para su posterior descarga
ID = []

#### Google Drive API ####

# Se comunica con la API
# Si se modifica esta parte, eliminar el archivo token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = None

# El archivo token.pickle almacena los tokens de acceso y actualización del usuario, y se 
# crea automáticamente cuando el flujo de autorización se completa por primera vez.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# Si no hay credenciales (válidas) disponibles, se permite que el usuario inicie sesión.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Se guardan las credenciales para la próxima ejecución.
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('drive', 'v3', credentials=creds)

# Función para listar los archivos que se encuentran en el Drive
def listFiles(size):
	# Lista los archivos
    results = service.files().list(pageSize=size, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        print('No se encontraron archivos.')
    else:
        print('Archivos:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

# Función para subir los archivos al Drive con el nombre "filename", la ruta
# del archivo "filepath" y el tipo de archivo "mimetype"
def uploadFile(filename,filepath,mimetype):
	file_metadata = {'name': filename}
	media = MediaFileUpload(filepath, mimetype=mimetype)
	file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
	# Se obtiene el id
	imagen_id = file.get('id')
	# Se guarda
	ID.append(imagen_id)
	# Se imprime
	print('ID Archivo: %s' % imagen_id)

# Función para descargar los archivos del Drive con la posicion del id en el 
# arreglo "indice_id" y la ruta del archivo "filepath"
def downloadFile(indice_id,filepath):
    file_id=ID[indice_id]
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
	# Ciclo para procesar la descarga
    while done is False:
        status, done = downloader.next_chunk()
		# Se imprime
        print("Descargando %d%%." % int(status.progress() * 100))
	with io.open(filepath,'wb') as f:
		fh.seek(0)
		f.write(fh.read())
	# Se borra la id de la lista
	ID.remove(file_id)

##########################

# Se comienzan a recorrer todos los cuadros
while True:
	# Se recibe el nombre y el frame del RPi del RPi y acusar recibo
	(rpiName, frame) = imageHub.recv_image()
	imageHub.send_reply(b'OK')

	# Si un dispositivo no está en el último diccionario activo, 
	# significa que es un dispositivo recién conectado
	if rpiName not in lastActive.keys():
		print("[INFO] Reciviendo datos de {}...".format(rpiName))

	# Se registra el último tiempo activo para el dispositivo del que 
	# acabamos de recibir un frame
	lastActive[rpiName] = datetime.now()

	# Se cambia el tamaño del frame para que tenga un ancho máximo de 400 píxeles, 
	# luego se toman las dimensiones del frame y se construye un blob
	frame = imutils.resize(frame, width=400)
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
		0.007843, (300, 300), 127.5)

	# Se pasa el blob a través de la red y se obtienen las detecciones y predicciones
	net.setInput(blob)
	detections = net.forward()

	# Se restable el recuento de objetos para cada objeto en el conjunto "CONSIDER"
	objCount = {obj: 0 for obj in CONSIDER}

	# Ciclo para recorrer las detecciones
	for i in np.arange(0, detections.shape[2]):
		# Se extrae la "confidencea" (es decir, la probabilidad) asociada con la predicción
		confidence = detections[0, 0, i, 2]

		# Se filtran las detecciones débiles asegurando que la "confidence" es mayor 
		# que la confianza mínima
		if confidence > args["confidence"]:
			# Se extrae el índice de la etiqueta de clase de las detecciones
			idx = int(detections[0, 0, i, 1])
			tiempo_final = time.time() 
			tiempo_transcurrido = tiempo_final - tiempo_inicial
			# Se hace una verificación de tiempo transcurrido para la siguiente captura
			# ademas de un control si la detección es de una persona
			if tiempo_transcurrido >= 5 and idx == 15:
				tiempo_inicial = time.time()
				# Se captura la imagen
				cv2.imwrite("Captura_%d.jpg" %contador, frame)
				print("[INFO] Subiendo captura")
				# Se sube al Drive
				uploadFile("Captura_%d.jpg" %contador,"Captura_%d.jpg" %contador,'image/jpeg')
				# Se borra localmente
				subprocess.call(["sudo","rm","Captura_%d.jpg" %contador])
				contador += 1

			# Se verifica si la clase predicha está en el conjunto de clases 
			# que deben considerarse
			if CLASSES[idx] in CONSIDER:
				# Se incrementa el recuento del objeto particular detectado en el frame
				objCount[CLASSES[idx]] += 1

				# Se calculan las coordenadas (x, y) del cuadro delimitador para el objeto
				box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
				(startX, startY, endX, endY) = box.astype("int")

				# Se dibuja el cuadro delimitador alrededor del objeto detectado en el frame
				cv2.rectangle(frame, (startX, startY), (endX, endY),
					(255, 0, 0), 2)

	# Se dibuja el nombre del dispositivo emisor en el frame
	cv2.putText(frame, rpiName, (10, 25),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

	# Se dibuja el recuento de objetos en el frame
	label = ", ".join("{}: {}".format(obj, count) for (obj, count) in
		objCount.items())
	cv2.putText(frame, label, (10, h - 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255,0), 2)

	# Se actualiza el nuevo frame en el diccionario de frames
	frameDict[rpiName] = frame

	# Se construye un montaje usando imágenes en el diccionario de frames
	montages = build_montages(frameDict.values(), (w, h), (mW, mH))

	# Se mostran los montajes en la pantalla
	for (i, montage) in enumerate(montages):
		cv2.imshow("Home pet location monitor ({})".format(i),
			montage)

	# Se detecta si se a pulsado cualquier tecla
	key = cv2.waitKey(1) & 0xFF

	# Si la hora actual 'menos' la última vez que se realizó la verificación del dispositivo 
	# activo es mayor que el umbral establecido, se realiza una verificación
	if (datetime.now() - lastActiveCheck).seconds > ACTIVE_CHECK_SECONDS:
		# Ciclo para recorrer todos los dispositivos previamente activos
		for (rpiName, ts) in list(lastActive.items()):
			# Se elimina el RPi de los últimos diccionarios activos y de frames si el 
			# dispositivo no ha estado activo recientemente
			if (datetime.now() - ts).seconds > ACTIVE_CHECK_SECONDS:
				print("[INFO] Coneccion perdida con {}".format(rpiName))
				lastActive.pop(rpiName)
				frameDict.pop(rpiName)

		# Se establece la última hora de verificación activa como hora actual
		lastActiveCheck = datetime.now()

	# Si se presionó la tecla 'q', que salga del bucle
	if key == ord("q"):
		break

# Se hace una limpieza
cv2.destroyAllWindows()