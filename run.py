import os
import socket
import uvicorn

def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0

def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return start_port

if __name__ == "__main__":
    env_port = os.getenv("PORT")
    if env_port:
        port = int(env_port)
        host = "0.0.0.0"
    else:
        port = find_available_port(8000)
        host = "127.0.0.1"
    print(f"Starting VirasatPlanner on http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
