import os, socket, threading, select, sys, traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import fulltest_udp_proto

serv_dir = ""

def run_udp(port):    
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, fulltest_udp_proto.UDP_BUFF_SIZE * 50)
    udp_socket.bind(('127.0.0.1', port))
    
    udp_processor = fulltest_udp_proto.UDPProcessor(serv_dir, udp_socket)
    while True:
        data, addr = udp_socket.recvfrom(fulltest_udp_proto.SEND_PACKET_LENGTH)
        #print(('Received UDP from %s:%s' % addr) + " length:" + str(len(data)))
        udp_processor.recv(data, addr)
                

class ServerHandler(BaseHTTPRequestHandler):
    mimedic = [
        ('.html', 'text/html'),
        ('.htm', 'text/html'),
        ('.js', 'application/javascript'),
        ('.css', 'text/css'),
        ('.json', 'application/json'),
        ('.png', 'image/png'),
        ('.jpg', 'image/jpeg'),
        ('.gif', 'image/gif'),
        ('.txt', 'text/plain'),
        ('.avi', 'video/x-msvideo'),
    ]    

    def do_GET(self):

        filepath = urlparse(self.path).path

        if filepath.endswith('/'):
            filepath += 'index.html'
        _, fileext = os.path.splitext(filepath)

        mimetype = None
        sendReply = False
        for e in ServerHandler.mimedic:
            if e[0] == fileext:
                mimetype = e[1]
                sendReply = True
                break

        if sendReply == True: 
            try:
                with open(os.path.realpath(serv_dir + filepath),'rb') as f:
                    content = f.read()
                    self.send_response(200)
                    self.send_header('Content-type',mimetype)
                    self.end_headers()
                    self.wfile.write(content)
            except :
                traceback.print_exc()
                self.send_error(404,'File Not Found: %s' % self.path)

    def do_POST(self) :
        try:
            filepath = urlparse(self.path).path
            content_len = int(self.headers.get('Content-Length'))
            post_body = self.rfile.read(content_len)
            
            with open(os.path.realpath(serv_dir + filepath),'rb') as f:
                content = f.read()
                self.send_response(200)
                self.send_header('Content-type','text/plain')
                self.end_headers()
                if content == post_body[2:]:
                    self.wfile.write(b"OK")
                else:
                    self.wfile.write(b"FAILED")
        except:
            traceback.print_exc()

def run(dir, port):
    if not os.path.exists(dir):
        print("can't find the directory [" + dir +"]")
        exit(1)
    else:
        global serv_dir
        serv_dir = dir + "/"

    t = threading.Thread(target = run_udp, args = (port,))
    t.daemon = True
    t.start()

    httpd = HTTPServer(('', port), ServerHandler)
    httpd.serve_forever()

if __name__ == '__main__':
    print(__file__ + " args " + str(sys.argv))
    if len(sys.argv) >= 3:  
        run(sys.argv[1], int(sys.argv[2]))
    else:
        run('html', 18080)