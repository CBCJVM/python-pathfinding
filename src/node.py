import math

class Node(object):
    def __init__(self, x, y):
        super(Node, self).__init__()
        self.x, self.y = float(x), float(y)
        self.visible_siblings = set()
    
    def dist(self, point):
        return math.hypot(self.x - point.x, self.y - point.y)
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"
    
    def __repr__(self):
        return "Node" + self.__str__()
    
    def __hash__(self):
        return hash(self.x)^hash(self.y)
