import os
import numpy
import socket
from dotenv import load_dotenv
import logging
from classes.history import HistoryEntry

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
    ACTION_S_GAME = "game"
    
    buffer = []
    direction = None
    pos = []
    last_pos = None
    wins = 0
    losses = 0
    map_dimensions = []
    goal = [0, 0]
    
    DIRECTIONS = ["up", "right", "down", "left"]
    
    history = numpy.ndarray((0,0))
    
    def __init__(self) -> None:
        load_dotenv()
        self.host = os.environ.get("GPN_MAZE_HOST")
        self.host6 = os.environ.get("GPN_MAZE_HOST6")
        self.port = int(os.environ.get("GPN_MAZE_PORT"))
        self.username = os.environ.get("GPN_BOT_USERNAME", "r2d2")
        self.password = os.environ.get("GPN_BOT_PASSWORD")
        
        logging.debug([self.host, self.host6, self.port, self.username, self.password])
        self.bootstrap()
        
        
        
    def connect(self):
        logging.debug("trying to connect via IPv4")
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(10)
        try:
            self.s.connect((self.host, self.port))
        except:
            logging.debug("connection via IPv4 failed, connecting via IPv6")
            self.s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            self.s.connect((self.host6, self.port))
        logging.debug("connected")
        
        
    def join(self):
        logging.debug("joining")
        self._send(f"{self.ACTION_JOIN}{self.SEPARATOR}{self.username}{self.SEPARATOR}{self.password}{self.ENDCHAR}")
        
        
    def bootstrap(self):
        self.connect()
        self.join()
        # self.send_chat_message(f"Hello world from {self.username}!")
        
        
    def init_history(self):
        if len(self.map_dimensions):
            self.history = numpy.empty((self.map_dimensions[0], self.map_dimensions[1]), dtype=HistoryEntry)
    
    
    def send_chat_message(self, msg):
        logging.debug(f"Chatting message: {msg}")
        self._send(f"{self.ACTION_CHAT}{self.SEPARATOR}{msg}{self.ENDCHAR}")
        
        
    def communicate(self):
        while True:
            lastlen = len(self.buffer)
            self.update_buffer()
            
            new_elems = self.buffer[lastlen-1:]
            for elem in new_elems:
                if elem:
                    logging.info(f"[SERVER] {elem}")
                    self.handle_buffer(elem)


    def update_buffer(self):
        for elem in self._recv().decode("utf-8").split("\n"):
            self.buffer.append(elem)
    
    
    def update_pos(self, pos):
        logging.debug(f"{self.pos=} {self.last_pos=}")
        if not self.last_pos:
            self.direction = [1,1,1,1]
            
            delta_x = pos[0] - self.goal[0]
            delta_y = pos[1] - self.goal[1]
            
            if abs(delta_x) > abs(delta_y):
                if delta_x > 0:
                    self.direction[1] = 0
                else:
                    self.direction[3] = 0
            else:
                if delta_y > 0:
                    self.direction[0] = 0
                else:
                    self.direction[2] = 0
            
            self.last_pos = pos
            self.pos = pos
            return
        
        self.last_pos = self.pos
        self.pos = pos
        
        list_direction = [
            self.last_pos[0] - self.pos[0],
            self.last_pos[1] - self.pos[1]
        ]
        logging.debug(f"{list_direction=}")
        
        direction = [1,1,1,1]
        
        # top
        direction[0] = 1
        # right
        direction[1] = 1
        # bottom
        direction[2] = 1
        # left
        direction[3] = 1
        
        # handle x axis
        if list_direction[0] != 0:
            if list_direction[0] < 0:
                direction[1] = 0
            else:
                direction[3] = 0

        # handle y axis
        if list_direction[1] != 0:
            if list_direction[1] > 0:
                direction[0] = 0
            else:
                direction[2] = 0
        
        self.direction = direction
        
            
    def move(self):
        index_of_direction = self.direction.index(0)
        logging.debug(f"{self.direction=}")
        
        index_of_direction = index_of_direction - 1
        
        if index_of_direction < 0:
            index_of_direction += 4
        
        for i in range(4):
            safe_index = index_of_direction + i
            
            if safe_index > 3:
                safe_index = safe_index - 4
                
            logging.debug(f"{safe_index=} {index_of_direction=}")
            
            if self.pos[safe_index + 2] == 0:
                next_move = safe_index
                break
        
        self.history[self.pos[0]][self.pos[1]] = HistoryEntry(walls=self.pos[2:], directions_taken=[1,1,1,1])
        logging.debug(self.history)
        self.send_move_msg(next_move)
    
    
    def send_move_msg(self, next_move):
        logging.info(f"Going {self.DIRECTIONS[next_move]}")
        self._send(
            f"{self.ACTION_MOVE}{self.SEPARATOR}{self.DIRECTIONS[next_move]}{self.ENDCHAR}"
        )


    def _send(self, msg):
        totalsent = 0
        logging.info(f"[CLIENT] {msg.strip()}")
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


    def nuke_everything(self):
        self.pos = []
        self.last_pos = None
        self.direction = None
        # self.history = numpy.ndarray((0,0))
    
    
    def handle_buffer(self, buffer):
        for attr in dir(self):
            if attr.startswith(self.PREFIX_SERVER):
                msg_as_list = buffer.split(self.SEPARATOR)
                s_param = msg_as_list[0]
                
                if s_param == self.ACTION_S_GAME:
                    int_list = list(map(lambda x: int(x), msg_as_list[1:]))
                    self.goal = int_list[2:4]
                    self.map_dimensions = int_list[0:2]
    
                    self.init_history()
                    
                    logging.debug(self.goal)
                    break
                
                if s_param == self.ACTION_S_POS:
                    int_pos = list(map(lambda x: int(x), msg_as_list[1:]))
                    self.update_pos(int_pos)
                    logging.debug(f"Position: x: {self.pos[0]} y: {self.pos[1]}")
                    logging.debug(f"Walls: {self.pos[2:]}")
                    
                    self.move()
                    break
                
                if s_param == self.ACTION_S_ERR:
                    raise Exception(msg_as_list[1])
                
                if s_param == self.ACTION_S_WIN:
                    logging.info("We won!")
                    logging.info(f"{self.wins=} {self.losses=}")
                    self.nuke_everything()
                    self.wins += 1
                    break
                
                if s_param == self.ACTION_S_LOSE:
                    logging.info("We lost")
                    logging.info(f"{self.wins=} {self.losses=}")
                    self.nuke_everything()
                    self.losses += 1
                    break