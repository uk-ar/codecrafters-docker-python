import subprocess
import sys
import os
import shutil
import ctypes

#from . import pull
import app.pull
import tarfile

# 名前空間の種類を表すフラグ
CLONE_NEWNS = 0x00020000  # マウント名前空間
CLONE_NEWUTS = 0x04000000  # UTS名前空間
CLONE_NEWIPC = 0x08000000  # IPC名前空間
CLONE_NEWUSER = 0x10000000  # ユーザー名前空間
CLONE_NEWPID = 0x20000000  # PID名前空間
CLONE_NEWNET = 0x40000000  # ネットワーク名前空間
CLONE_NEWCGROUP = 0x02000000  # cgroup名前空間

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    # print("Logs from your program will appear here!")

    # Uncomment this block to pass the first stage
    #
    print(sys.argv)
    name, *reference = sys.argv[2].split(":")
    if not reference:
        reference = "latest"

    layers = app.pull.docker_pull(name,reference)
    for layer in layers:
        with tarfile.open(layer,'r:gz') as tar:
            tar.extractall(path='./tmp')

    command = sys.argv[3]
    args = sys.argv[4:]

    print("./tmp"+os.path.dirname(command))
    os.makedirs("./tmp"+os.path.dirname(command),exist_ok=True)
    #shutil.copy2(command,"./tmp"+command)

    # unshareシステムコールを呼び出す
    libc = ctypes.CDLL('libc.so.6')
    result = libc.unshare(CLONE_NEWPID)

    #if result != 0:
    #    raise OSError(ctypes.get_errno())

    completed_process = subprocess.run(["chroot","./tmp",command, *args], capture_output=True)
    print(completed_process.stdout.decode("utf-8"), end="")
    print(completed_process.stderr.decode("utf-8"), file=sys.stderr, end="")

    #shutil.rmtree("./tmp")
    exit(completed_process.returncode)    

if __name__ == "__main__":
    main()
