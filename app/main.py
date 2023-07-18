import subprocess
import sys
import os
import shutil

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    # print("Logs from your program will appear here!")

    # Uncomment this block to pass the first stage
    #
    
    command = sys.argv[3]
    args = sys.argv[4:]

    os.mkdir("./tmp")
    os.makedirs("./tmp"+os.path.dirname(command))
    shutil.copy2(command,"./tmp"+command)

    completed_process = subprocess.run(["chroot","./tmp",command, *args], capture_output=True)
    print(completed_process.stdout.decode("utf-8"), end="")
    print(completed_process.stderr.decode("utf-8"), file=sys.stderr, end="")

    shutil.rmtree("./tmp")
    exit(completed_process.returncode)    

if __name__ == "__main__":
    main()
