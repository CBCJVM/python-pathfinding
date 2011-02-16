import geometry
import node

class Board(object):
    """Representing a game board, this class is composed of a set of
    ``Polygon``s which are non-moveable. These can represent PVC, blocks, or any
    other place you wish for the robot to avoid. Knowing everything about the
    game's design, this class can do such things as tell if a node is within the
    line-of-sight or another node, or even utilize Dijkstra's algorithm to find
    the shortest possible path from one node to another. Note that this board is
    not entirely realistic. It assumes each node is simply an infinitely tiny
    point in space, and that robots are nodes. For realistic purposes, a wrapper
    or extended version of this class could be used."""
    
    def __init__(self):
        """Creates an empty board. Use the ``add`` function"""
        super(Board, self).__init__()
        self.polygons = set()
        self.__precalculated = False
    
    def add(self, poly):
        """Adds a polygon, ``poly``, to the game board."""
        self.polygons.add(poly)
        self.__precalculated = False
    
    def remove(self, poly):
        """Removes a polygon, ``poly``, from the game board."""
        self.polygons.remove(poly)
        self.__precalculated = False
    
    def get_lines(self):
        """Creates and returns a set of every polygon's lines on this
        ``Board``."""
        lines = set()
        for i in self.polygons:
            lines.update(i.lines)
        return lines
    
    def get_expanded(self, outset):
        b = Board()
        for p in self.polygons:
            b.add(p.get_expanded(outset))
        return b
    
    def __str__(self):
        return str(self.polygons)[4:-1]
    
    lines = property(get_lines,
                     doc="A set of every ``Polygon``'s lines on this ``Board``")
    
    def get_nodes(self):
        """Creates and returns a set of every polygon's nodes on this
        ``Board``."""
        nodes = set()
        for i in self.polygons:
            nodes.update(i.nodes)
        return nodes
    
    nodes = property(get_nodes,
                     doc="A set of every ``Polygon``'s nodes on this ``Board``")
    
    def precalculate_visibility(self):
        """Before doing a group of visibility tests, call this first, and it can
        do some caching that may improve the performance of further is_visible
        calls. You don't need to call this before calling ``get_shortest_path``,
        as it will intelligently decide if it should call this or not, and if
        so, it will do it itself."""
        if self.__precalculated: return False
        for i in self.nodes:
            i.visible_siblings = set()
            i.nonvisible_siblings = set()
        for i in self.nodes:
            for k in self.nodes:
                if not k is i and k not in i.visible_siblings and \
                   k not in i.nonvisible_siblings:
                    if self.__visibility_test(i, k):
                        i.visible_siblings.add(k)
                        k.visible_siblings.add(i)
                    else:
                        i.nonvisible_siblings.add(k)
                        k.nonvisible_siblings.add(i)
        for i in self.nodes: # cleanup
            del i.nonvisible_siblings
        self.__precalculated = True
        return True
    
    def __visibility_test(self, node_a, node_b):
        """Performs a simple direct visibility test between two points, in an
        unoptimized fashion"""
        # Todo: ensure visibility checks cannot go through polygons (facepalm)
        direct_line = geometry.Line(node_a, node_b)
        for p in self.polygons:
            for l in p.lines:
                if l.does_intersect(direct_line, False):
                    return False
            for l in p.triangle_lines:
                if l.does_intersect(direct_line, False):
                    return False
            if direct_line in p.triangle_lines: return False
        return True # survived all the tests
    
    def is_visible(self, node_a, node_b):
        if self.__precalculated:
            if node_a in node_b.visible_siblings:
                return True
            if node_a in self.nodes and node_b in self.nodes:
                # must have been determined to be nonvisible
                return False
        # when all else fails...
        return self.__visibility_test(node_a, node_b)
    
    def get_visible_set(self, pov, *args):
        """Returns a set of nodes that are visible to the first argument. The
        nodes checked are the map's internal set of nodes, as well as any nodes
        given after the first argument."""
        visible_set = self.get_visible_set_for(pov, *args)
        for i in self.nodes:
            if self.is_visible(pov, i) and pov != i: visible_set.add(i)
        return visible_set
    
    def get_visible_set_for(self, pov, *args):
        """Returns a set of nodes that are visible to the first argument. The
        nodes checked are only the nodes given after the first argument."""
        visible_set = set()
        for i in args:
            if self.is_visible(pov, i) and pov != i: visible_set.add(i)
        return visible_set
       
    def get_shortest_path(self, node_a, node_b):
        self.precalculate_visibility()
        
        # Handle special/common cases
        if node_a == node_b: return [node_a]
        if self.is_visible(node_a, node_b): return [node_b] # direct is shortest
        
        # Format: shortest_to[node] = (goes_though, cost, is_minimum)
        shortest_to = {node_b:None}
        for i in self.nodes:
            shortest_to[i] = None
        starting_from = node_a
        starting_from_cost = 0
        while True:
            # find possible paths
            improvable = set()
            for k in shortest_to:
                if shortest_to[k] == None or not shortest_to[k][2]:
                    improvable.add(k)
            improvable &= self.get_visible_set(starting_from, node_b)
            if not improvable: # nothing else we can do
                return None
            # see if there is a shorter path for any of these via starting_from
            lowest_cost = None
            lowest_cost_node = None
            for i in improvable:
                cost = starting_from_cost + starting_from.dist(i)
                if not lowest_cost or cost < lowest_cost:
                    lowest_cost = cost
                    lowest_cost_node = i
                if not shortest_to[i] or cost < shortest_to[i][1]:
                    shortest_to[i] = (starting_from, cost, False)
            lowest_cost_info = list(shortest_to[lowest_cost_node])
            lowest_cost_info[2] = True
            shortest_to[lowest_cost_node] = tuple(lowest_cost_info)
            if lowest_cost_node == node_b: # we're done! wrap it up.
                path = []
                n = node_b
                while n != node_a:
                    path[:0] = [n]
                    n = shortest_to[n][0]
                return path
            starting_from = lowest_cost_node
            starting_from_cost = lowest_cost
