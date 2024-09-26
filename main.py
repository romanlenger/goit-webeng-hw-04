import json
import urllib.parse
import os
import threading
import socket

from pathlib import Path
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer

BASE_DIR = Path()
BUFFER_SIZE = 1024


class MyFramework(SimpleHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        print(route.query)
        match route.path:
            case '/':
                self.send_html(os.path.join('Module4', 'HW', 'index.html'))
            case '/message.html':
                self.send_html(os.path.join('Module4', 'HW', 'message.html'))
            case '/404':
                self.send_html(os.path.join('Module4', 'HW', 'error.html'))
            case _:
                self.send_html(os.path.join('Module4', 'HW', 'error.html'), status_code=404)

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            message_data = self.parse_post_data(post_data.decode())

            self.send_data_via_socket(message_data)

            self.send_response(302)
            self.send_header('Location', '/message.html')
            self.end_headers()

    def send_html(self, filename, status_code=200):
        try:
            self.send_response(status_code)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            with open(filename, 'rb') as file:
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"File not found")

    def parse_post_data(self, post_data):
        fields = dict(x.split('=') for x in post_data.split('&'))
        return {
            "username": fields.get('username', ''),
            "message": fields.get('message', '')
        }

    def send_data_via_socket(self, message_data):
        server_address = ('localhost', 5000)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            message_bytes = json.dumps(message_data).encode('utf-8')
            sock.sendto(message_bytes, server_address)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            message_data = json.loads(msg.decode('utf-8'))
            timestamp = datetime.now().isoformat()
            save_message_to_file(timestamp, message_data)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()


def save_message_to_file(timestamp, message):
    file_path = os.path.join('Module4', 'HW', 'storage', 'data.json')
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    data[timestamp] = message

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def run_server():
    address = ('localhost', 3000)
    http_server = HTTPServer(address, MyFramework)
    print("HTTP сервер запущено на порту 3000")

    socket_thread = threading.Thread(target=run_socket_server, args=('localhost', 5000))
    socket_thread.daemon = True
    socket_thread.start()

    http_server.serve_forever()


if __name__ == "__main__":
    run_server()
