import hashlib
import os

# GLOBALS
configDict = dict()
filesAndHashes = dict()
newFilesAndHashes = dict()


def folderHash(pathName):
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
    splittedPathsToHash = configDict["Directories to protect"].split(
        ",")  # para ser mejor, hacer strip con un for para cada elemento por si acaso
    for path in splittedPathsToHash:
        filesAndHashes.update(folderHash(path))
    with open("hashes.hash", "w") as writer:
        for key, value in filesAndHashes.items():
            writer.write(key + "=" + value + "\n")


def importHashedFiles():
    with open("hashes.hash", "r") as reader:
        line = reader.readline()
        while line:
            splittedLineList = line.split("=")
            newFilesAndHashes[splittedLineList[0].replace(
                "\n", "")] = splittedLineList[1].replace("\n", "")
            line = reader.readline()
    # print(newFilesAndHashes)


def calculateHashedFiles():
    splittedPathsToHash = configDict["Directories to protect"].split(
        ",")  # para ser mejor, hacer strip con un for para cada elemento por si acaso
    for path in splittedPathsToHash:
        filesAndHashes.update(folderHash(path))


def compareHashes():
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
