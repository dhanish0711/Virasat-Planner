import uvicorn
import socket

def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) != 0

def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return start_port

if __name__ == "__main__":
    port = find_available_port(8000)
    print(f"Starting VirasatPlanner on http://127.0.0.1:{port}")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
