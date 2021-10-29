# SchoolSecurity
_El programa permite ejecutar la captura de video en un ordenadores de placa reducida y procesar la imagen en un ordenador separado con mayor capacidad de computo, el cual al momento de detectar una anomalia sube el fotograma exacto en el que se detecto dicha amenaza a la cuenta de google drive del operario para hacer el respectivo analisis._

## 🚀 Introducción
La inseguridad es un tópico de gran interés por parte de los ciudadanos, esto debido a que el hurto es de los delitos mas comunes a lo largo de todo el país. En base a esto nos enfocamos principalmente en la seguridad en instituciones educativas, ya que estos lugares están expuestos a este tipo de problemas, la solución que comúnmente se implementa es el instalar cámaras para compensar esta falta den seguridad. Pero hay un inconveniente, ya que la revisión del material de seguridad se hace a mano, lo cual es algo engorroso de hacer.

### Por qué
Las instituciones educativas de nivel primaria y básica son un foco comun para actos delictivos, expendio de estupefacientes o robos por parte de personas ajenas al establecimiento. En el mundo actual donde la tecnología esta avanzando rápidamente, ya es posible detectar a estas personas sin la necesidad de tener personal adicional.

### Cómo
Se implementará sobre la infraestructura de camaras de vigilancia en las instituciones educativas, un sistema que detectara automaticamente a personas que intenten acercarse con intensiones malintencionadas a esta, que alertaran mediante una alarma a una aplicación.

### Qué
Se pretende usar un modelo de Deep Learning para detectar personas en areas de poco movimiento, la presencia de personas en un vıdeo de camaras de vigilancia. Utilizando Python y OpenCV. Una vez implementado este modelo, lo integramos con una interfaz web para supervisar y gestionar las capturas. Finalmente  para complemetar el proyecto con los temas vistos en la electiva, proponemos un modelo 3D disenado  en OnShape e implementado en Ultimaker Cura para la base de instalacion de la camara, que no sea muy llamativo, con el fin deque pase desapercibido.

## 📋 Pre-requisitos

Es necesario tener dos maquinas, en este caso se usó una Raspberry Pi como cliente y un ordenador como servidor, ademas se deben completar las credenciales del archivo [credentials.json](credentials.json)

## 🔧 Instalación

_Servidor_
```
python server.py
```

_Cliente_
```
python client.py
```

## 🛠️ Construcción

* [Python](https://www.python.org/) - Lenguaje
* [OpenCV](https://opencv.org/) - Libreria IA visión de maquina
* [OnShape](https://www.onshape.com/) - Modelado 3D

## ✒️ Autores

* **Luis Felpe López Pardo** - *Desarrollo* - [lopepardo](https://github.com/lopepardo)
* **Kevin Muñoz Rengifo** - *Desarrollo* - [kevinmuz55](https://github.com/kevinmuz55)
* **Juan Manuel Solis Prado** - *Desarrollo* - [SlowProgrammer](https://github.com/SlowProgrammer)

También puedes ver la lista de todos los [contribuyentes](https://github.com/kevinmuz55/SchoolSecurity/contributors) quíenes han participado en este proyecto. 

## 🎁 Expresiones de Gratitud

* Agradecimientos al curso de sistemas ubicuos de la Universidad del Cauca
