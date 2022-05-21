from calendar import different_locale
from cmath import log
import os
import socket
from dotenv import load_dotenv
import logging

class Bot:
    
    SEPARATOR = "|"
    ENDCHAR = "\n"
    
    # client packets
    ACTION_JOIN = "join"
    ACTION_MOVE = "move"
    ACTION_CHAT = "chat"
    
    # server packts
    PREFIX_SERVER = "ACTION_S"
    ACTION_S_MOTD = "motd"
    ACTION_S_ERR = "error"
    ACTION_S_POS = "pos"
    ACTION_S_WIN = "win"
    ACTION_S_LOSE = "lose"
    ACTION_S_GOAL = "goal"
    
    buffer = []
    direction = None
    _current_pos = []
    _pos_history = []
    
    def __init__(self) -> None:
        load_dotenv()
        self.host = os.environ.get("GPN_MAZE_HOST")
        self.port = int(os.environ.get("GPN_MAZE_PORT"))
        self.username = os.environ.get("GPN_BOT_USERNAME", "r2d2")
        self.password = os.environ.get("GPN_BOT_PASSWORD")
        
        logging.debug(self.host, self.port, self.username, self.password)
        self.bootstrap()
        
    def connect(self):
        logging.debug("trying to connect")
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))
        logging.debug("connected")
        
    def join(self):
        logging.debug("joining")
        self._send(f"{self.ACTION_JOIN}{self.SEPARATOR}{self.username}{self.SEPARATOR}{self.password}{self.ENDCHAR}")
        
    def bootstrap(self):
        self.connect()
        self.join()
        self.send_chat_message(f"Hello world from {self.username}!")
    
    def send_chat_message(self, msg):
        logging.debug(f"Chatting message: {msg}")
        self._send(f"{self.ACTION_CHAT}{self.SEPARATOR}{msg}{self.ENDCHAR}")
        
    def communicate(self):
        while True:
            lastlen = len(self.buffer)
            self.update_buffer()
            
            new_elems = self.buffer[lastlen-1:]
            for elem in new_elems:
                logging.debug(f"REPLY: {elem}")
                self.handle_buffer(elem)

    def update_buffer(self):
        for elem in self._recv().decode("utf-8").split("\n"):
            self.buffer.append(elem)

    def _send(self, msg):
        totalsent = 0
        msg = msg.encode()
        sent = self.s.send(msg[totalsent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent

    def _recv(self):
        chunks = []
        bytes_recd = 0
        chunk = self.s.recv(2048)
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)
    
    def handle_buffer(self, buffer):
        for attr in dir(self):
            if attr.startswith(self.PREFIX_SERVER):
                msg_as_list = buffer.split(self.SEPARATOR)
                s_param = msg_as_list[0]
                
                if s_param == self.ACTION_S_GOAL:
                    self.goal = msg_as_list[1:]
                    logging.debug(self.goal)
                    break
                
                if s_param == self.ACTION_S_POS:
                    self.pos = msg_as_list[1:]
                    logging.debug(self.pos)
                    break
                
                if s_param == self.ACTION_S_ERR:
                    raise Exception(msg_as_list[1])