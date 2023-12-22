
def GetCurrentVersion():
    # Check the Version.txt file that lives inside the git-managed folder
    file = open("../MagicMirror/Version.txt", "r")
    version = int(file.readline())
    file.close()
    return version