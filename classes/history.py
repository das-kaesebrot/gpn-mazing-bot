class HistoryEntry:
    
    walls = None
    directions_taken = None
    visited = False
    
    def __init__(
        self,
        walls: list,
        directions_taken: list
        ) -> None:
        
        self.walls = walls
        self.directions_taken = directions_taken
        
    def is_dead_end(self) -> bool:
        pass