import hashlib
import os

# GLOBALS
configDict = dict()
filesAndHashes = dict()
newFilesAndHashes = dict()


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
                fileAndHash[os.path.join(root, file).replace("\\", "/")] = hashlib.sha256(
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
            print("¡La configuración se ha cargado correctamente!")
            # print(configDict)
        except:
            print("¡No se ha podido cargar la configuracion, revisa la sintaxis!")
    else:
        configs = ["Selected Hash=\n",
                   "Directories to protect=\n", "Verify interval=\n"]
        try:
            with open("config.config", "w") as file:
                file.write(
                    "# To list directories, write them separated by comma\n# Interval time in minutes")
                for config in configs:
                    file.write(config)
            print("¡Archivo de configuración creado!")
        except:
            print(
                "¡No se ha podido crear el archivo de configuración, revisa los permisos!")


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


def importHashedFiles():
    """ Params: NONE """
    """ Return: NONE """
    """ Lee el archivo 'hashes.hash' y carga cada una de las entradas en el diccionario 'newFilesAndHashes' presente en el script """
    with open("hashes.hash", "r") as reader:
        line = reader.readline()
        while line:
            splittedLineList = line.split("=")
            newFilesAndHashes[splittedLineList[0].replace(
                "\n", "")] = splittedLineList[1].replace("\n", "")
            line = reader.readline()
    # print(newFilesAndHashes)


def calculateHashedFiles():
    """ Params: NONE """
    """ Return: NONE """
    """ Calcula los hashes de los archivos nuevamente, y reutilizamos el diccionario creado al principio 'filesAndHashes' esto servirá
    para comparar los items de este diccionario con los del 'newFilesAndHashes'. """
    splittedPathsToHash = configDict["Directories to protect"].split(
        ",")  # para ser mejor, hacer strip con un for para cada elemento por si acaso
    for path in splittedPathsToHash:
        filesAndHashes.update(folderHash(path))


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
    print("\nNumber of files OK: " + str(numberOfFilesOK))
    print("Number of files BAD: " + str(numberOfFilesNoOk))
    print("BAD integrity files: ")
    print('\n '.join(listOfNoMatches))


importConfig()
importHashedFiles()
calculateHashedFiles()
compareHashes()

# exportHashedFiles()
