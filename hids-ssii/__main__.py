import hashlib
import os
import time
import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import logging
import tkinter as tk
import threading
import sys
from threading import Thread
from tkinter.scrolledtext import ScrolledText
from tkinter import *
from tkinter import messagebox
from win10toast import ToastNotifier
import smtplib
from pathlib import Path
from arbol import Arbol
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# GLOBALS
configDict = dict()
badIntegrity = list()
graphDate = list()
arbol = Arbol()
report = list()
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
verifyInterval = 0
reportInterval = 0
running = bool()
window = tk.Tk()
entry = ScrolledText(window, width=80, height=20)
logBox = ScrolledText(window, width=80, height=20)
toaster = ToastNotifier()



# Genera una estructura en forma de árbol binario a partir de los directorios escogidos para las comprobaciones de integridad, cada nodo del arbol es una tupla (ruta,hash)
# Donde el hash se realizará de acuerdo al tipo indicado en el fichero de configuración.
def binaryTreeHash(pathName, arbol):
    for root, dirs, files in os.walk(pathName):
        for file in files:
            with open(os.path.join(root, file), "rb") as fileRaw:   
                if(configDict["Selected Hash mode"].lower() == "sha3_512"):
                    arbol.agregar((os.path.join(root, file).replace("\\", "/"),hashlib.sha3_512(
                        fileRaw.read()).hexdigest()))
                elif(configDict["Selected Hash mode"].lower() == "sha3_384"):
                    arbol.agregar((os.path.join(root, file).replace("\\", "/"),hashlib.sha3_384(
                        fileRaw.read()).hexdigest()))                    
                #Por defecto dejaremos cifrado sha-256
                else:
                    arbol.agregar((os.path.join(root, file).replace("\\", "/"),hashlib.sha3_256(
                        fileRaw.read()).hexdigest()))


           
def readLogFile():
    text = str()
    if (os.path.exists(os.path.join('c:/hids-ssii', 'log.log'))):
        with open(os.path.join('c:/hids-ssii', 'log.log')) as reader:
            text = reader.read()
    else:
        f = open(os.path.join('C:\\hids-ssii', 'log.log'), "x")
    return text


def logBoxContainer():
    logBox.delete("1.0", tk.END)
    text = readLogFile()
    logBox.insert(tk.INSERT, text)
    logBox.insert(tk.END, "")


def importConfig():
    """ Params: NONE """
    """ Return: NONE """
    """ Crea un archivo de configuración si no lo hay con las opciones de la plantilla de 'configs'
    y en caso de que ya exista (que sería siempre menos la primera vez que se ejecute el script)
    carga la configuración de dicho archivo y la importa al diccionario del script llamado 'configDict',
    mediante este diccionario vamos a poder manejar dichas opciones indicadas en el archivo de configuración"""
    path = os.path.abspath('.').split(os.path.sep)[
        0]+os.path.sep+"hids-ssii\config.config"
    if (os.path.exists(path)):
        try:
            with open(path, "r") as config:
                for line in config:
                    if "#" not in line:
                        confSplitted = line.split("=")
                        configDict[confSplitted[0].strip(
                        )] = confSplitted[1].strip()

                        entry.insert(tk.INSERT, confSplitted[0].strip(
                        ) + "=" + confSplitted[1].strip() + "\n")

                    else:
                        entry.insert(tk.INSERT, line)
                    entry.insert(tk.END, "")
            logging.info("La configuración se ha importado correctamente!")
            # entry.insert(tk.END, " in ScrolledText")
            # print(configDict)
        except:
            logging.error("Error al importar la configuración!")
    else:
        configs = ["\nSelected Hash mode=\n",
                   "Directories to protect=\n", "Verify interval=\n", "Report interval=\n" "email=\n", "smtpPass=\n", "toEmail=\n"]
        try:
            with open(os.path.abspath('.').split(os.path.sep)[0]+os.path.sep+"hids-ssii\config.config", "w") as file:
                file.write(
                    "# Agregar los directorios a proteger, separados por una coma\n# Intervalo de tiempo entre examenes en minutos\n# Guardar la configuracion antes de iniciar el examen")
                for config in configs:
                    file.write(config)
            logging.info("Archivo de configuración creado satisfactoriamente!")

        except:
            logging.error(
                "Error al crear el archivo de configuración, problema con los permisos?")
        importConfig()


def exportConfig():
    """ Params: NONE """
    """ Return: NONE """
    """ Escribe en el archivo 'C:\hids-ssii\config.config' las configuraciones reflejadas en la caja de texto del script """
    with open(os.path.abspath('.').split(os.path.sep)[0]+os.path.sep+"hids-ssii\config.config", "w") as config:
        config.write(entry.get("1.0", tk.END))


def exportHashedFiles():
    """ Params: NONE """
    """ Return: NONE """
    """ Comprueba las rutas que hemos indicado en el archivo de configuración y carga todos los archivos de cada una
    de ellas gracias a la función anterior 'binaryTreeHash', una vez hecho esto crea un archivo 'hashes.hash' si no lo hay y escribe
    en el todas las rutas junto a su hash, separadas mediante un simbolo '=' """
    # TIME
    global arbol #Se pone global para dejar claro que vamos a utilizar una varible global y evitar que busque una variable local en su lugar
    begin_time = datetime.datetime.now()
    splittedPathsToHash = configDict["Directories to protect"].split(
        ",")  # para ser mejor, hacer strip con un for para cada elemento por si acaso
    for path in splittedPathsToHash:
        binaryTreeHash(path, arbol) 
    end = datetime.datetime.now()-begin_time
    strr = "Hashes exportados correctamente en: " + str(end)
    print("Hemos creado el árbol en: " + str(end))
    logging.info(strr)


#Cambiar

def compareHashes():
    """ Params: NONE """
    """ Return: NONE """
    """ Compara los dos diccionarios, uno contiene los hashes cargados del archivo hashes.hash y el otro contiene los hashes recien calculados,
    tras dicha comparación los resultados saldran por consola """
    numberOfFilesOK = int()
    numberOfFilesNoOk = int()
    listOfNoMatches = list()
    global report
    arbolActual = Arbol()
    splittedPathsToHash = configDict["Directories to protect"].split(
        ",")  # para ser mejor, hacer strip con un for para cada elemento por si acaso
    for path in splittedPathsToHash:
        binaryTreeHash(path, arbolActual)
    tupleTree = arbol.recorrer()
    dictArbol = dict(tupleTree)
    tupleActual = arbolActual.recorrer()
    dictArbolActual = dict(tupleActual)
    #Comprobamos las rutas de los ficheros que hay actualmente en el sistema de archivos con las que había cuando se inició
    #el HIDS para el directorio/s que sea
    value = { k : dictArbol[k] for k in set(dictArbol) - set(dictArbolActual) }
    for fichero in value:
        numberOfFilesNoOk += 1
        cadena = "DIR: " + str(fichero) + " ¡Archivo eliminado detectado!"
        listOfNoMatches.append(cadena)

    value2 = { k : dictArbolActual[k] for k in set(dictArbolActual) - set(dictArbol) }
    for fichero in value2:
        numberOfFilesNoOk += 1
        cadena = "DIR: " + str(fichero) + " ¡Archivo nuevo detectado!"
        listOfNoMatches.append(cadena)
        aux = (fichero, value2[fichero])
        tupleActual.remove(aux)
    #z = {**value, **value2}

    for tupla in tupleActual:
        try:
            nodoGuardado = arbol.buscar(tupla)
            if nodoGuardado.dato[1] == tupla[1]:
                numberOfFilesOK += 1
            else:
                numberOfFilesNoOk += 1
                cadena = "DIR: " + str(tupla[0]) + " ¡Los hashes no coinciden!"
                listOfNoMatches.append(cadena)
        except:
            numberOfFilesNoOk += 1
            cadena = "DIR: " + str(tupla[0]) + " ¡Los hashes no coinciden!"
            listOfNoMatches.append(cadena)
    badIntegrity.append(numberOfFilesNoOk)

    fechaHora = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    graphDate.append(fechaHora)
    str1 = "Número de archivos OK: " + str(numberOfFilesOK)
    str2 = "Número de archivos MODIFICADOS: " + str(numberOfFilesNoOk)
    
    report.append(fechaHora + "\n")
    report.append(str1 + "\n")
    report.append(str2 + "\n")

    #ESTE PODRÍA QUITARSE
    logging.info(str1)
    logging.info(str2)

    if(listOfNoMatches):
        str3 = "Archivos con integridad comprometida: "
        noMatchesToPrint = list()
        for entry in listOfNoMatches:
            noMatchesToPrint.append("           "+entry)
        logging.warning(str3 + "\n" + '\n'.join(noMatchesToPrint))
        toaster.show_toast(
            "HIDS", "Problema de integridad detectado. Revisar LOG.", duration=verifyInterval, threaded=True)
        sendEmails(str3 + "\n" + '\n'.join(noMatchesToPrint))
        report.append(str3 + "\n" + '\n'.join(noMatchesToPrint))
    report.append("--------------------------------------------------------------------\n")


#Método que permite enviar mensajes al destinatario deseado, indicando los problemas de integridad detectados por el HIDS en el directorio analizado y 
# envía mensaje en caso de que el sistema se detenga
def sendEmails(directorios):

    
    remitente = str(configDict["email"])
    password = str(configDict["smtpPass"])
    destinatario = str(configDict["toEmail"])
    asunto = "Problema de integridad"
    body = "El HIDS ha detectado una integridad comprometida, por favor revise el siguiente log para conocer más detalles: "+ "\n"+ directorios

    # Creamos la conexión con el servidor
    sesion_smtp = smtplib.SMTP('smtp.gmail.com', 587)

    # Ciframos la conexión
    sesion_smtp.starttls()

    # Iniciamos sesión en el servidor
    sesion_smtp.login(remitente, password)


    # Creamos el objeto mensaje
    mensaje = MIMEMultipart()

    # Establecemos los atributos del mensaje
    mensaje['From'] = remitente
    mensaje['To'] = destinatario
    mensaje['Subject'] = asunto

    # Agregamos el cuerpo del mensaje como objeto MIME de tipo texto
    mensaje.attach(MIMEText(body, 'plain'))


    # Convertimos el objeto mensaje a texto
    texto = mensaje.as_string()

    # Enviamos el mensaje
    sesion_smtp.sendmail(remitente, destinatario, texto)

    # Cerramos la conexión
    sesion_smtp.quit()
    print("Se han enviado los correos correctamente.")

#Método que verifica la integridad
def run():
    if running == True:
        begin_time = datetime.datetime.now()
        compareHashes()
        logBox.config(state=tk.NORMAL)
        logBoxContainer()  # AQUI EL LOG BOX
        logBox.config(state=tk.DISABLED)
        threading.Timer(float(verifyInterval), run).start()
        end = datetime.datetime.now() - begin_time
        strr = "Comprobación realizada con éxito en: " + str(end)
        logging.info(strr)

#Método que genera el reporte con los datos recogidos de las verificaciones
def runReport():
    if running == True:
        fechaHora = datetime.datetime.now().strftime("%d-%m-%Y_%H %M %S")
        with open("Report " + fechaHora + ".txt", "w") as file:
            for line in report:
                file.write(line)

        threading.Timer(float(reportInterval), runReport).start()
        toaster.show_toast("HIDS", "Examen finalizado. Reporte generado.", duration=reportInterval, threaded=True)
        logging.info("Examen finalizado. Reporte generado.")

# Método que inicializa los hilos cuando se ejecutan el exámen 
def runHandle():
    t = Thread(target=run)
    #Vaciamos la lista del report para que no haya información de examenes anteriores cancelados
    global report
    report.clear()
    global running
    running = True
    t.start()
    threading.Timer(float(reportInterval), runReport).start()

# Método que inicia el exámen de comprobación de la integridad
def initExam():
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(100)
    root_logger = logging.getLogger("")
    root_logger.addHandler(console)
    global verifyInterval
    global reportInterval
    verifyInterval = int(configDict["Verify interval"])
    reportInterval = int(configDict["Report interval"])
    # supuestamente el admin nos pasa a nosotros el hasheado de todos los archivos -> Si no, ejecutar exportHashedFiles()
    exportHashedFiles()
    runHandle()

#Método que permite interrumpir el servicio de comprobación de la integridad y hace una llamada a sendEmails() para notificar
def stop():
    toaster.show_toast(
        "HIDS", "Servicio interrumpido. El sistema NO está examinando los directorios.", threaded=True)
    global running
    running = False
    logging.critical("EXAMEN INTERRUMPIDO")
    sendEmails("El HIDS se ha detenido, no se están realizando comprobaciones de integridad sobre su sistema de archivos.")


#Método que permite interrumpir el servicio de comprobación de la integridad cuando se cierra la aplicación y hace una llamada a sendEmails() para notificar
def stopAndClose():
    global running
    running = False
    logging.critical("HIDS CERRADO")
    #sendEmails(username, password, "El HIDS se ha detenido, no se están realizando comprobaciones de integridad sobre su sistema de archivos.")
    os._exit(1)


#Método que genera la interfaz de usuario del HIDS
def gui():

    window.resizable(0, 0)
    window.geometry("1340x512")
    
    
    labelInicio = tk.Label(window, text="Iniciar el examen ")
    labelStop = tk.Label(window, text="Parar el examen ")
    labelConf = tk.Label(window, text="Fichero de configuración")
    labelLog = tk.Label(window, text="Fichero de LOG")
    labelInicio.pack()
    labelInicio.place(x=510, y=410)
    labelStop.pack()
    labelStop.place(x=800, y=410)
    labelConf.pack()
    labelConf.place(x=640, y=410)
    labelLog.pack()
    labelLog.place(x=630, y=350)
    window.title("HIDS Security Team 23")
    btnIniciar = tk.Button(window, text="Iniciar",
                           command=initExam)
    btnIniciar.pack(pady=15, padx=15)
    btnIniciar.place(x=535, y=435)
    btnCerrar = tk.Button(window, text="Parar", command=stop)
    btnCerrar.pack(pady=15, padx=15)
    btnCerrar.place(x=825, y=435)
    btnGuardar = tk.Button(
        window, text="Importar configuración", command=importConfig)
    btnGuardar.pack(pady=15, padx=15)
    btnGuardar.place(x=640, y=435)
    logBox.pack()
    logBox.place(x=370, y=24)
    window.protocol("WM_DELETE_WINDOW", stopAndClose)
    window.mainloop()


# Método que inicializa la aplicación, lee los logs e importa la configuración además de cargar la interfaz de usuario
def iniciar():
    try:
        Path("C:\\hids-ssii").mkdir(parents=True)
    except:
        pass
    readLogFile()
    filename = os.path.abspath('.').split(os.path.sep)[
        0]+os.path.sep+"hids-ssii\log.log"
    logging.basicConfig(format='%(levelname)s:%(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S', filename=filename, level=logging.INFO)
    importConfig()
    gui()


if __name__ == "__main__":
    iniciar()
