import subprocess
import pystray
from PIL import Image, ImageDraw

server_process = None
project_path = r"D:\xamp\htdocs\autocad_system"

def start_server(icon, item):
    global server_process
    if not server_process:
        server_process = subprocess.Popen(
            ["python", "manage.py", "runserver", "0.0.0.0:8000"],
            cwd=project_path
        )
    else:
        print("Server already running")

def stop_server(icon, item):
    global server_process
    if server_process:
        server_process.terminate()
        server_process = None

def create_image():
    # Create a simple tray icon (a white square on blue background)
    image = Image.new("RGB", (64, 64), (30, 100, 200))
    d = ImageDraw.Draw(image)
    d.rectangle((16, 16, 48, 48), fill=(255, 255, 255))
    return image

icon = pystray.Icon("AutoCADSystem", create_image(), "AutoCAD System", menu=pystray.Menu(
    pystray.MenuItem("Start Server", start_server),
    pystray.MenuItem("Stop Server", stop_server),
    pystray.MenuItem("Exit", lambda icon, item: icon.stop())
))

icon.run()
