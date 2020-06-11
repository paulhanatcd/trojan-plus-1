import urllib, os, threading, traceback, socket, select, time
from concurrent.futures import ThreadPoolExecutor , as_completed

SEND_PACKET_LENGTH = 8192
UDP_BUFF_SIZE = 1024 * 1024

UDP_INDEX_HEADER_SIZE = 1

client_udp_bind_port_start = 30000
server_udp_send_port_start = 40000

def bind_port(udp_socket, port):
    try_max_count = 10
    offset = 1000
    port_increase = 0
    for _ in range(0, try_max_count):
        try:
            udp_socket.bind(("", port + port_increase))
            return
        except:
            port_increase = offset
            offset = offset + 1

    raise Exception("[ERROR] Cannot bind a new port for udp socket!")

def send_udp_file_data(udp_socket, port, addr, content):
    content_setment_len = SEND_PACKET_LENGTH - UDP_INDEX_HEADER_SIZE
    index = 0
    i = 0
    while i < len(content):
        
        send_content = index.to_bytes(1, 'big') + content[i:i + content_setment_len]
        sent = udp_socket.sendto(send_content, addr)

        #print(" send_udp_file_data index: " + str(index) + " sent: " + str(sent))

        if sent > 0:
            i = i + sent - UDP_INDEX_HEADER_SIZE
            index = index + 1
        else:
            raise Exception("udp sendto failed!")

        # wait for a while, otherwise server will flood client in pipeline mode, avoid dropping udp packet
        # in forward mode, client only has one socket to recv
        if index % 5 == 0:
            time.sleep(0.01)         

def compose_udp_file_data(data_arr):
    sorted(data_arr, key = lambda d : d[0])
    data = b''
    for d in data_arr:
        data = data + d[1:]
    return data

def send_get_func(serv_dir, addr, udp_data, port):
    try:
        with open(os.path.realpath(serv_dir + udp_data.file()),'rb') as f:
            content = f.read()
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as us :
                bind_port(us, port)
                us.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, UDP_BUFF_SIZE)
                send_udp_file_data(us, port, addr, content)
    except:
        traceback.print_exc()

class UDPData:

    def __init__(self, args, data):
        self.data_arr = []
        self.args = args
        self.total_length = int(self.args["len"])
        self.recv_length = 0

        if len(data) > 1:
            self.append(data)

    def append(self, data):
        self.data_arr.append(data)
        self.recv_length = self.recv_length + len(data) - UDP_INDEX_HEADER_SIZE

    def file(self):
        return self.args["file"]

    def file_length(self):
        return self.total_length

    def method(self):
        return self.args["m"]

    def compose_data(self):
        return compose_udp_file_data(self.data_arr)
    
class UDPProcessor:

    def __init__(self, serv_dir, udp_socket):
        self.serv_dir = serv_dir
        self.executor = ThreadPoolExecutor(max_workers = 10)
        self.udp_socket = udp_socket
        self.recv_map={}

    def recv(self, data, addr):
        udp_data = None
        if addr in self.recv_map:
            udp_data = self.recv_map[addr]
            udp_data.append(data)
        else:
            args_idx = data.index(b'\r\n')
            args = dict(urllib.parse.parse_qsl(data[:args_idx].decode('ascii')))
            udp_data = UDPData(args, data[args_idx + 2:])
            self.recv_map[addr] = udp_data
        
        global server_udp_send_port_start
        if udp_data.method() == 'GET' :
            self.executor.submit(send_get_func, self.serv_dir, addr, udp_data, server_udp_send_port_start)
            server_udp_send_port_start = server_udp_send_port_start + 1
        else:
            #print('udp_data.recv_length  == ' + str(udp_data.recv_length) + ' udp_data.file_length() == '+ str(udp_data.file_length()))
            if udp_data.recv_length == udp_data.file_length():
                self.executor.submit(self.post_data, addr, self.recv_map[addr], server_udp_send_port_start)
                self.recv_map.pop(addr)
                server_udp_send_port_start = server_udp_send_port_start + 1

    def post_data(self, addr, udp_data, port):
        with open(os.path.realpath(self.serv_dir + udp_data.file()),'rb') as f:
            cmp_content = f.read()
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as us :
                bind_port(us, port)
                us.sendto(b'OK' if cmp_content == udp_data.compose_data() else b'FAILED', addr)