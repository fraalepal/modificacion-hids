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
from win10toast import ToastNotifier
import smtplib

# GLOBALS
configDict = dict()
filesAndHashes = dict()
newFilesAndHashes = dict()
badIntegrity = list()
graphDate = list()
cantidadDeArchivos = [0, 1000]
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
interval = 0
running = bool()
window = tk.Tk()
entry = ScrolledText(window, width=80, height=20)
logBox = ScrolledText(window, width=80, height=20)
toaster = ToastNotifier()


def folderHash(pathName):
    """ Params: ruta """
    """ Return: devuelve un diccionario formato por la ruta y el hash: key=ruta, value=hash """
    """ Se le pasa una ruta y viaja por todos los archivos y las subrutas de dicha ruta y calcula los hashes
    de cada uno de los archivos encontrados """
    fileAndHash = dict()
    for root, dirs, files in os.walk(pathName):
        for file in files:
            with open(os.path.join(root, file), "rb") as fileRaw:
                # Habria q hacer algo para poder elegir entre multiples algoritmos de hash
                # de todas formas he añadido la opcion de elegir en el archivo config.config
                if(configDict["Selected Hash mode"] == "sha3_256"):
                    fileAndHash[os.path.join(root, file).replace("\\", "/")] = hashlib.sha3_256(
                        fileRaw.read()).hexdigest()
                elif(configDict["Selected Hash mode"] == "sha3_384"):
                    fileAndHash[os.path.join(root, file).replace("\\", "/")] = hashlib.sha3_384(
                        fileRaw.read()).hexdigest()
                elif(configDict["Selected Hash mode"] == "sha3_512"):
                    fileAndHash[os.path.join(root, file).replace("\\", "/")] = hashlib.sha3_512(
                        fileRaw.read()).hexdigest()
                elif(configDict["Selected Hash mode"] == "md5"):
                    fileAndHash[os.path.join(root, file).replace("\\", "/")] = hashlib.md5(
                        fileRaw.read()).hexdigest()
    return fileAndHash


def readLogFile():
    text = str()
    if (os.path.exists(os.path.join('c:/top_secret', 'log.log'))):
        with open(os.path.join('c:/top_secret', 'log.log')) as reader:
            text = reader.read()
    else:
        f = open(os.path.join('C:\\top_secret', 'log.log'), "x")
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
        0]+os.path.sep+"top_secret\config.config"
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
                   "Directories to protect=\n", "Verify interval=\n", "email=\n", "smtpPass=\n", "toEmail=\n"]
        try:
            with open(os.path.abspath('.').split(os.path.sep)[0]+os.path.sep+"top_secret\config.config", "w") as file:
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
    """ Escribe en el archivo 'C:\top_secret\config.config' las configuraciones reflejadas en la caja de texto del script """
    with open(os.path.abspath('.').split(os.path.sep)[0]+os.path.sep+"top_secret\config.config", "w") as config:
        config.write(entry.get("1.0", tk.END))


def exportHashedFiles():
    """ Params: NONE """
    """ Return: NONE """
    """ Comprueba las rutas que hemos indicado en el archivo de configuración y carga todos los archivos de cada una
    de ellas gracias a la función anterior 'folderHash', una vez hecho esto crea un archivo 'hashes.hash' si no lo hay y escribe
    en el todas las rutas junto a su hash, separadas mediante un simbolo '=' """
    splittedPathsToHash = configDict["Directories to protect"].split(
        ",")  # para ser mejor, hacer strip con un for para cada elemento por si acaso
    for path in splittedPathsToHash:
        filesAndHashes.update(folderHash(path))
    with open(os.path.abspath('.').split(os.path.sep)[0]+os.path.sep+"top_secret\hashes.hash", "w") as writer:
        for key, value in filesAndHashes.items():
            writer.write(key + "=" + value + "\n")
    logging.info("Hashes exportados correctamente")


def importHashedFiles():
    """ Params: NONE """
    """ Return: NONE """
    """ Lee el archivo 'C:\top_secret\hashes.hash' y carga cada una de las entradas en el diccionario 'newFilesAndHashes' presente en el script """
    try:
        with open(os.path.abspath('.').split(os.path.sep)[0]+os.path.sep+"top_secret\hashes.hash", "r") as reader:
            line = reader.readline()
            while line:
                splittedLineList = line.split("=")
                newFilesAndHashes[splittedLineList[0].replace(
                    "\n", "")] = splittedLineList[1].replace("\n", "")
                line = reader.readline()
        logging.info("Hashes importados correctamente!")
    except:
        logging.error("Error al importar los hashes!")
        # print(newFilesAndHashes)


def calculateHashedFiles():
    """ Params: NONE """
    """ Return: NONE """
    """ Calcula los hashes de los archivos nuevamente, y reutilizamos el diccionario creado al principio 'filesAndHashes' esto servirá
    para comparar los items de este diccionario con los del 'newFilesAndHashes'. """
    logging.info("Calculando los hashes de los archivos...")
    splittedPathsToHash = configDict["Directories to protect"].split(
        ",")  # para ser mejor, hacer strip con un for para cada elemento por si acaso
    for path in splittedPathsToHash:
        filesAndHashes.update(folderHash(path))
    logging.info("Hashes calculados satisfactoriamente!")


def compareHashes():
    """ Params: NONE """
    """ Return: NONE """
    """ Compara los dos diccionarios, uno contiene los hashes cargados del archivo hashes.hash y el otro contiene los hashes recien calculados,
    tras dicha comparación los resultados saldran por consola """
    numberOfFilesOK = int()
    numberOfFilesNoOk = int()
    listOfNoMatches = list()
    for key, value in filesAndHashes.items():
        if newFilesAndHashes[key] == value:
            numberOfFilesOK += 1
        else:
            numberOfFilesNoOk += 1
            cadena = "DIR: " + str(key) + " HASHES DOESN'T MATCH!"
            listOfNoMatches.append(cadena)
    badIntegrity.append(numberOfFilesNoOk)
    graphDate.append(datetime.datetime.now().strftime("%M"))
    str1 = "Number of files OK: " + str(numberOfFilesOK)
    str2 = "Number of files BAD: " + str(numberOfFilesNoOk)
    logging.info(str1)
    logging.info(str2)
    if(listOfNoMatches):
        str3 = "BAD integrity files: "
        noMatchesToPrint = list()
        for entry in listOfNoMatches:
            noMatchesToPrint.append("           "+entry)
        logging.warning(str3 + "\n" + '\n'.join(noMatchesToPrint))
        toaster.show_toast(
            "HIDS", "Hay un problema integridad. Revisar LOG.", duration=interval, threaded=True)
        sendEmail(str3 + "\n" + '\n'.join(noMatchesToPrint))
    else:
        toaster.show_toast(
            "HIDS", "Examen finalizado. Se mantiene la integridad.", duration=interval, threaded=True)


def graph():
    """ Params: NONE """
    """ Return: NONE """
    """ Muestra una gráfica en el navegador en base a los datos de las dos listas 'badIntegrity' y 'graphDate' """
    layout_title = "Evolución de la integridad de los archivos fecha:  " + \
        str(datetime.datetime.now().strftime("%d-%m-%Y"))
    df = pd.DataFrame(dict(
        x=graphDate,
        y=badIntegrity
    ))
    fig = px.bar(df,
                 x='x', y='y',
                 color_discrete_sequence=[
                     'red']*3,
                 title=layout_title,
                 labels={'x': 'Dia', 'y': 'Numero de fallos de integridad'})
    fig.show()


def run():
    """ Params: NONE """
    """ Return: NONE """
    """  """
    if running == True:
        calculateHashedFiles()
        compareHashes()
        logBox.config(state=tk.NORMAL)
        logBoxContainer()  # AQUI EL LOG BOX
        logBox.config(state=tk.DISABLED)
        # graph()
        threading.Timer(float(interval), run).start()


def runHandle():
    t = Thread(target=run)
    global running
    running = True
    t.start()


def initExam():
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(100)
    root_logger = logging.getLogger("")
    root_logger.addHandler(console)
    global interval
    interval = int(configDict["Verify interval"])
    # supuestamente el admin nos pasa a nosotros el hasheado de todos los archivos -> Si no, ejecutar exportHashedFiles()
    exportHashedFiles()
    importHashedFiles()
    runHandle()


def sendEmail(bodyMsg):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()

        server.login(configDict["email"], configDict["smtpPass"])
        subject = "¡Problema con la integridad de los archivos!"
        body = bodyMsg
        msg = f"Subject: {subject}\n\n{body}".encode('utf-8')
        emailList = configDict["toEmail"].split(",")
        for email in emailList:
            server.sendmail("gigi.dan2011@gmail.com", email, msg)
        server.quit()
    except:
        print("Ha ocurrido un error enviando el mensaje.")


def gui():
    window.resizable(0, 0)
    window.geometry("1340x512")
    labelInicio = tk.Label(window, text="Iniciar el examen ")
    labelStop = tk.Label(window, text="Parar el examen ")
    labelGraph = tk.Label(window, text="Abrir gráfico ")
    labelConf = tk.Label(window, text="Fichero de configuración")
    labelLog = tk.Label(window, text="Fichero de LOG")
    labelInicio.pack()
    labelInicio.place(x=510, y=410)
    labelStop.pack()
    labelStop.place(x=728, y=410)
    labelGraph.pack()
    labelGraph.place(x=630, y=410)
    labelConf.pack()
    labelConf.place(x=230, y=333)
    labelLog.pack()
    labelLog.place(x=950, y=333)
    entry.pack()
    entry.place(x=5, y=0)
    window.title("HIDS")
    btnGraph = tk.Button(window, text="Abrir grafico", command=graph)
    btnGraph.pack(pady=15, padx=15)
    btnGraph.place(x=628, y=435)
    btnIniciar = tk.Button(window, text="Iniciar",
                           command=initExam)
    btnIniciar.pack(pady=15, padx=15)
    btnIniciar.place(x=535, y=435)
    btnCerrar = tk.Button(window, text="Parar", command=stop)
    btnCerrar.pack(pady=15, padx=15)
    btnCerrar.place(x=751, y=435)
    btnGuardar = tk.Button(
        window, text="Guardar configuración", command=exportConfig)
    btnGuardar.pack(pady=15, padx=15)
    btnGuardar.place(x=532, y=330)
    logBox.pack()
    logBox.place(x=670, y=0)
    window.protocol("WM_DELETE_WINDOW", stopAndClose)
    window.mainloop()


def stop():
    toaster.show_toast(
        "HIDS", "Servicio interrumpido. El sistema NO está examinando los directorios.", threaded=True)
    global running
    running = False
    logging.critical("EXAMEN INTERRUMPIDO")


def stopAndClose():
    global running
    running = False
    logging.critical("HIDS CERRADO")
    os._exit(1)


def iniciar():

    readLogFile()
    filename = os.path.abspath('.').split(os.path.sep)[
        0]+os.path.sep+"top_secret\log.log"
    logging.basicConfig(format='%(levelname)s:%(asctime)s: %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S', filename=filename, level=logging.INFO)
    importConfig()
    gui()


if __name__ == "__main__":
    iniciar()
