
def GetCurrentVersion(sourcePath):
    # Check the Version.txt file that lives inside the git-managed folder
    file = open(sourcePath + "/Version.txt", "r")
    version = int(file.readline())
    file.close()
    return version