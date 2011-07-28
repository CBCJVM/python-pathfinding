import node
import math

class Line(object):
    """The name of this class can be misleading. It represents a line segment.
    Line objects are represented by two Node object"""
    
    def __init__(self, node_a=None, node_b=None, slope=None, distance=None):
        """Constructs a Line from ``node_a`` extending to ``node_b``. As a
        shorthand, each node in the constructor can be written as a tuple, and
        will simply be converted to Nodes upon construction. The slope and
        distance arguments can be used if only one node is known. With a
        positive distance, the unknown node is defined as to the right. With a
        negative distance, the unknown node is defined as to the left of the
        known node. If slope is infinite, the unknown point is defined as above,
        if the slope is negative infinity, the unknown point is defined as
        below. Negative distance reverses this behavior"""
        super(Line, self).__init__()
        if isinstance(node_a, tuple):
            node_a = node.Node(*node_a)
        if isinstance(node_b, tuple):
            node_b = node.Node(*node_b)
        if node_a is None and node_b is None:
            raise Exception("At least one node must be defined")
       	if node_a is None:
       	    node_a = self.__get_other_node(node_b, slope, distance)
       	if node_b is None:
       	    node_b = self.__get_other_node(node_a, slope, distance)
        self.node_a, self.node_b = node_a, node_b
        self.midpoint = node.Node((node_a.x + node_b.x)*.5,
                                  (node_a.y + node_b.y)*.5)
    
    def __get_other_node(self, n, slope, distance):
        # alternatively...
        # x = d/sqrt(m*m+1)
        # y = dm/sqrt(m*m+1)
        ang = math.atan(slope)
        return node.Node(n.x + distance * math.cos(ang),
                         n.y + distance * math.sin(ang))
    
    def get_length(self):
        return self.node_a.dist(self.node_b)
    
    length = property(get_length,
                      doc="The distance from ``node_a`` to ``node_b``")
    
    def get_delta_x(self):
        return self.node_b.x - self.node_a.x
    
    delta_x = property(get_delta_x,
                       doc="""The horizontal distance, or the change in ``x``
                       from ``node_a`` to ``node_b``""")
    
    def get_delta_y(self):
        return self.node_b.y - self.node_a.y
    
    delta_y = property(get_delta_y,
                       doc="""The vertical distance, or the change in ``y`` from
                       ``node_a`` to ``node_b``""")
    
    def get_slope(self):
        if abs(self.delta_x) < 1e-7:
            if self.delta_y > 0:
                return float("inf")
            return float("-inf")
        return self.delta_y / self.delta_x
    
    slope = property(get_slope)
    
    def get_perpendicular_slope(self):
        if abs(self.delta_y) < 1e-7:
            if self.delta_x > 0:
                return float("-inf")
            return float("inf")
        return -self.delta_x / self.delta_y
    
    perpendicular_slope = property(get_perpendicular_slope)
    
    def does_intersect(self, other, vertexes_count=True):
        """Uses the algorithm defined here:
        http://www.bryceboe.com/2006/10/23/line-segment-intersection-algorithm/
        Along with some special handlers for edge-cases (no pun intended).
        """
        # the algorithm doesn't handle parallel lines, so let's check that first
        # we'll cross-multiply the slopes, and then compare them
        if self.delta_x * other.delta_y == self.delta_y * other.delta_x:
            return False
        
        # define our shorthand
        a, b = self.node_a, self.node_b
        c, d = other.node_a, other.node_b
        return self.__ccw(a, c, d) != self.__ccw(b, c, d) and \
               self.__ccw(a, b, c) != self.__ccw(a, b, d) and \
               (vertexes_count or (a != c and a != d and b != c and b != d))
    
    def __ccw(self, a, b, c):
        """A utility function for ``does_intersect``."""
        return (c.y - a.y) * (b.x - a.x) > (b.y - a.y) * (c.x - a.x)
    
    def __eq__(self, other):
        return (self.node_a == other.node_a and self.node_b == other.node_b) or\
               (self.node_a == other.node_b and self.node_b == other.node_a)
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash(self.node_a) ^ hash(self.node_b)

class BasePolygon(object):
    """This class and it's subclasses should be assumed to be immutable, for
    performance sake"""
    def __init__(self, *nodes):
        super(BasePolygon, self).__init__()
        nodes = list(nodes)
        
        # convert shorthand tuples to nodes
        for i in range(len(nodes)):
            if isinstance(nodes[i], tuple):
                nodes[i] = node.Node(*nodes[i])
        
        # handler for if somebody completes the polygon (first node = last node)
        if nodes[-1] == nodes[0]:
            del nodes[-1]
        
        assert len(nodes) >= 3
        
        self.nodes = nodes
        
        lines = []
        for i in range(len(nodes)):
            # (i + 1) % len(nodes) essentially handles the circular nature of
            # the polygon, it is for the last in the list of nodes
            lines.append(Line(nodes[i], nodes[(i + 1) % len(nodes)]))
        self.lines = lines
        
        self.perimeter = sum([l.length for l in self.lines])
    
    def contains_node_in_area(self, node):
        """Based on/ported from some code donated ad hoc (public domain) by
        asarkar of #xkcd-cs on irc.foonetic.net"""
        result = False
        # because I'm too lazy of a porter to change all the variable names
        # within
        poly = list(self.nodes)
        poly.append(poly[0])
        p = node
        eps = 1e-7 # a value considered "close enough" to 0
        for i in xrange(1, len(poly)):
            p1 = poly[i];
            p2 = poly[i - 1];
            if p1.x < p.x and p2.x < p.x:
                # the segment is strictly to the left of the test point, so it
                # can't intersect the ray cast in the positive x direction
                continue
            elif p == p2:
                # the point is one of the vertices
                return True
            elif abs(p1.y - p.y) < eps and abs(p2.y - p.y) < eps:
                # the segment is horizontal
                if p.x >= min(p1.x, p2.x) and p.x <= max(p1.x, p2.x):
                    # the point is on the segment
                    return True
                # otherwise, don't count the segment
            elif (p1.y > p.y and p2.y <= p.y) or (p2.y > p.y and p1.y <= p.y):
                # non-horizontal upward edges include start, exclude end;
                # non-horizontal downward edges exclude start, include end
                det = (p1.x - p.x) * (p2.y - p.y) - (p1.y - p.y) * (p2.x - p.x)
                if abs(det) < eps:
                    # point is on the translated segment
                    return True
                if p2.y < p1.y:
                    det *= -1
                if det > 0:
                    # segment crosses if the determinant is positive
                    result = not result
        return result
    
    def __str__(self):
        s = "("
        for i in self.nodes:
            s += str(i)
        return s + ")"
    
    def __repr__(self):
        return "BasePolygon" + str(self)

class Triangle(BasePolygon):
    """A three-sided, three-vertexed polygon. Has some more features than
    Polygon, simply because there are more assumptions that can be made about
    triangles.
    
    Contains some ported code donated ad hoc (public domain) by asarkar of
    #xkcd-cs on irc.foonetic.net"""
    def __init__(self, *nodes):
        super(Triangle, self).__init__(*nodes)
        assert len(self.nodes) == 3
        # find area with modified Heron's formula. Area is positive if the node
        # list was in ccw order, negative if it was in cw order
        p, q, r = self.nodes
        self.area = .5 * (-q.x * p.y + r.x * p.y + p.x * q.y - r.x * q.y - p.x *
                          r.y + q.x * r.y)
        self.is_ccw = True
        if self.area < 0:
            self.area *= -1
            self.is_ccw = False
    
    def does_intersect_line(self, line):
        for l in self.lines:
            if l.does_intersect(line): return True
        return False
    
    def __repr__(self):
        return "Triangle" + str(self)

class Polygon(BasePolygon):
    """A polygon is created with a list of nodes, and is internally represented
    by list of nodes and a list of lines, in the order that they are given.
    
    Contains some ported code donated ad hoc (public domain) by asarkar of
    #xkcd-cs on irc.foonetic.net"""
    def __init__(self, *nodes, **kwargs):
        super(Polygon, self).__init__(*nodes)
        # perform triangulation
        if "ccw" in kwargs:
            ccw = kwargs["ccw"]
        ccw = True
        copy = list(self.nodes)
        # Convert this copy to CCW order
        # Step One: Determine what order it is to start with
        #angles = [math.atan2(i.delta_y, i.delta_x) for i in self.lines] # absang
        # make angles relative to each other
        #for i in xrange(len(angles)):
        #    a = (angles[i] - angles[(i - 1) % len(angles)]) % 360
        #    if a > 180:
        #        a -= 360
        #    angles[i] = a
        #if sum(angles) > 0:
        #    self.is_ccw = False
        #    copy.reverse()
        #else: self.is_ccw = True
        self.is_ccw = ccw
        if self.is_ccw:
            pass
        else:
            copy.reverse()
        result = []
        while len(copy) >= 3:
            t = Triangle(copy[0], copy[1], copy[2])
            is_ear = t.is_ccw and \
                     self.contains_node_in_area(Line(copy[0], copy[2]).midpoint)
            
            i = 3
            while is_ear and i < len(copy):
                if t.contains_node_in_area(copy[i]):
                    print "ear: ", copy[:3], ", err: ", copy[i]
                    is_ear = False
                i += 1
            
            if is_ear:
                # print "found ear: ", copy[:3]
                result.append(t)
                copy.pop(1)
            else:
                p = copy.pop(0)
                copy.append(p)
        self.triangles = result
        self.triangle_lines = set()
        for t in self.triangles:
            self.triangle_lines.update(t.lines)
        self.triangle_lines.difference_update(self.lines)
        e = Exception("Polygon is self-intersecting")
        for i in self.lines:
            for k in self.lines:
                if i.does_intersect(k, False):
                    raise e
    
    def does_intersect_line(self, line):
        if line in self.triangle_lines: return True
        for t in self.triangles:
            if t.does_intersect_line(line): return True
        return False
    
    def __repr__(self):
        return "Polygon" + str(self)
    
    def get_expanded(self, outset):
        n = self.nodes if self.is_ccw else list(reversed(self.nodes))
        inf = float("inf")
        # neg_zero = float("-0")
        point_slopes = []
        for i in xrange(len(n)):
            l = Line(n[i], n[(i + 1) % len(n)])
            s = l.slope
            p_s = l.perpendicular_slope
            # Perpendicular Line
            # Solve for quads, we deal with y on line because that corresponds
            # with the sign of x on the perp
            p_l = Line(node_a=l.midpoint, slope=p_s,
                       distance=(outset if l.delta_y < 0 else -outset))
            n_b = p_l.node_b
            point_slopes.append((n_b, s))
        # convert point_slopes to a series of points
        nodes = []
        for i in xrange(len(point_slopes)):
            nodes.append(self.__find_interesection_point(
                             *(point_slopes[i] +
                               point_slopes[(i + 1) % len(point_slopes)])))
        return Polygon(*nodes, ccw=True)
        
    def __find_interesection_point(self, pa, sa, pb, sb):
        """point in line a, slope of line a, point in line b, slope of line b"""
        inf = float("inf")
        if abs(sa) == inf and abs(sb) == inf or sa == sb:
            raise Exception("Parallel Lines")
        if abs(sa) == inf:
            return self.__find_interesection_point_inf(pa, pb, sb)
        if abs(sb) == inf:
            return self.__find_interesection_point_inf(pb, pa, sa)
        ba = pa.y - pa.x * sa
        bb = pb.y - pb.x * sb
        x = (bb - ba) / (sa - sb)
        return node.Node(x, sa * x + ba)
    
    def __find_interesection_point_inf(self, pa, pb, sb):
        return node.Node(pa.x, (pa.x - pb.x) * sb + pb.y)
    
    def get_nearest_outter_node(self, start):
        if not self.contains_node_in_area(start):
            return start
        for l in self.lines:
            pass
