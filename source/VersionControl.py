
def GetCurrentVersion():
    file = open("../Version.txt", "r")
    version = int(file.readline())
    file.close()
    return version