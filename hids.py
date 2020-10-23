import hashlib
import os

# GLOBALS
configDict = dict()
filesAndHashes = dict()


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
                    confSplitted = line.split("=")
                    configDict[confSplitted[0].strip(
                    )] = confSplitted[1].strip()
            print("¡La configuración se ha cargado correctamente!")
            print(configDict)
        except:
            print("¡No se ha podido cargar la configuracion, revisa la sintaxis!")
    else:
        configs = ["Selected Hash=\n", "Directories to protect=\n"]
        try:
            with open("config.config", "w") as file:
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


# def loadHashedFiles():
# def checkIntegrity():
"""folderHash(
    "C:/Users/Marcel/OneDrive - UNIVERSIDAD DE SEVILLA/GitHub/carpetaEjemplo")
"""
importConfig()
exportHashedFiles()
