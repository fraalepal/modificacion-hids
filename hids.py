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
from threading import Thread

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


def importConfig():
    """ Params: NONE """
    """ Return: NONE """
    """ Crea un archivo de configuración si no lo hay con las opciones de la plantilla de 'configs'
    y en caso de que ya exista (que sería siempre menos la primera vez que se ejecute el script)
    carga la configuración de dicho archivo y la importa al diccionario del script llamado 'configDict',
    mediante este diccionario vamos a poder manejar dichas opciones indicadas en el archivo de configuración"""
    if (os.path.exists("config.config")):
        try:
            with open("config.config", "r") as config:
                for line in config:
                    if "#" not in line:
                        confSplitted = line.split("=")
                        configDict[confSplitted[0].strip(
                        )] = confSplitted[1].strip()
            logging.info(
                str(now) + " La configuración se ha importado correctamente!")
            # print(configDict)
        except:
            logging.error(str(now) + " Error al importar la configuración!")
    else:
        configs = ["\nSelected Hash mode=\n",
                   "Directories to protect=\n", "Verify interval=\n"]
        try:
            with open("config.config", "w") as file:
                file.write(
                    "# To list directories, write them separated by comma\n# Interval time in minutes")
                for config in configs:
                    file.write(config)
            logging.info(
                str(now) + " Archivo de configuración creado satisfactoriamente!")

        except:
            logging.error(str(
                now) + " Error al crear el archivo de configuración, problema con los permisos?")


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
    with open("hashes.hash", "w") as writer:
        for key, value in filesAndHashes.items():
            writer.write(key + "=" + value + "\n")
    logging.info(str(now) + " Hashes exportados correctamente")


def importHashedFiles():
    """ Params: NONE """
    """ Return: NONE """
    """ Lee el archivo 'hashes.hash' y carga cada una de las entradas en el diccionario 'newFilesAndHashes' presente en el script """
    try:
        with open("hashes.hash", "r") as reader:
            line = reader.readline()
            while line:
                splittedLineList = line.split("=")
                newFilesAndHashes[splittedLineList[0].replace(
                    "\n", "")] = splittedLineList[1].replace("\n", "")
                line = reader.readline()
        logging.info(str(now) + " Hashes importados correctamente!")
    except:
        logging.error(str(now) + " Error al importar los hashes!")
        # print(newFilesAndHashes)


def calculateHashedFiles():
    """ Params: NONE """
    """ Return: NONE """
    """ Calcula los hashes de los archivos nuevamente, y reutilizamos el diccionario creado al principio 'filesAndHashes' esto servirá
    para comparar los items de este diccionario con los del 'newFilesAndHashes'. """
    logging.info(str(now) + " Calculando los hashes de los archivos...")
    splittedPathsToHash = configDict["Directories to protect"].split(
        ",")  # para ser mejor, hacer strip con un for para cada elemento por si acaso
    for path in splittedPathsToHash:
        filesAndHashes.update(folderHash(path))
    logging.info(str(now) + " Hashes calculados satisfactoriamente!")


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
    str1 = str(now) + " Number of files OK: " + str(numberOfFilesOK)
    str2 = str(now) + " Number of files BAD: " + str(numberOfFilesNoOk)
    logging.info(str1)
    logging.info(str2)
    if(listOfNoMatches):
        str3 = str(now) + " BAD integrity files: "
        # str4 = str(now) + '\n'.join(listOfNoMatches) # no funciona el tabulamiento con esto
        # logging.warning(str3)
        noMatchesToPrint = list()
        for entry in listOfNoMatches:
            noMatchesToPrint.append("           "+entry)
        logging.warning(str3 + "\n" + '\n'.join(noMatchesToPrint))


def graph():
    """ Params: NONE """
    """ Return: NONE """
    """ Muestra una gráfica en el navegador en base a los datos de las dos listas 'badIntegrity' y 'graphDate' """
    layout_title = "Evolución de la integridad de los archivos fecha:  " + \
        str(datetime.datetime.now().strftime("%d-%m-%Y"))
    # fig = go.Figure(data=[go.Bar(y=badIntegrity, x=graphDate)],layout_title_text = layout_title)

    df = pd.DataFrame(dict(
        x=graphDate,
        y=badIntegrity
    ))
    fig = px.bar(df,
                 x='x', y='y',  # data from df columns
                 # color_discrete_sequence=['red']*3
                 color_discrete_sequence=[
                     'red']*3,
                 title=layout_title,
                 labels={'x': 'Dia', 'y': 'Numero de fallos de integridad'})
    # dictionary = dict(zip(graphDate, badIntegrity))
    # data = pd.DataFrame([dictionary])
    fig.show()


def run():
    if running == True:
        calculateHashedFiles()
        compareHashes()
        # graph()
        threading.Timer(float(interval), run).start()


def runHandle():
    t = Thread(target=run)
    global running
    running = True
    t.start()


def init():
    logging.basicConfig(filename='log.log', level=logging.INFO)
    importConfig()
    global interval
    interval = int(configDict["Verify interval"])
    # supuestamente el admin nos pasa a nosotros el hasheado de todos los archivos
    exportHashedFiles()
    importHashedFiles()
    runHandle()


def gui():
    window = tk.Tk()
    window.title("HIDS")
    btn = tk.Button(window, text="Iniciar", command=init)
    btn.grid(column=1, row=0)
    btnCerrar = tk.Button(window, text="Cerrar", command=stop)
    btnCerrar.grid(column=2, row=0)
    window.protocol("WM_DELETE_WINDOW", stopAndClose)
    window.mainloop()


def stop():
    global running
    running = False
    logging.warning(str(now) + " EXAMEN INTERRUMPIDO")
    # os._exit(1)


def stopAndClose():
    global running
    running = False
    logging.warning(str(now) + " HIDS CERRADO")
    os._exit(1)


# run()
gui()
