# -*- coding: utf-8 -*-
import math

from utils import Point, CircleEvent, Arc, Segment, PriorityQueue


class Voronoi:
    def __init__(self, points, lowest, highest):
        self.final_line_segments = []  # list of line segment
        self.arc = None  # beach line

        self.sites = PriorityQueue()
        self.circles = PriorityQueue()

        # bounding box of size 0
        self.x0 = float(lowest)
        self.x1 = float(lowest)
        self.y0 = float(highest)
        self.y1 = float(highest)

        # insert points to site event
        for pts in points:
            point = Point(pts[0], pts[1])
            self.sites.push(point)
            # keep track of bounding box size
            if point.x < self.x0: self.x0 = point.x
            if point.y < self.y0: self.y0 = point.y
            if point.x > self.x1: self.x1 = point.x
            if point.y > self.y1: self.y1 = point.y

        # add margins to the bounding box
        self.add_margin_to_bounds()

    def add_margin_to_bounds(self):
        dx = (self.x1 - self.x0 + 1) / 5.0
        dy = (self.y1 - self.y0 + 1) / 5.0
        self.x0 = self.x0 - dx
        self.x1 = self.x1 + dx
        self.y0 = self.y0 - dy
        self.y1 = self.y1 + dy

    def process(self):
        while not self.sites.empty():
            if not self.circles.empty() and (self.circles.top().x <= self.sites.top().x):
                self.process_circle()  # handle circle event
            else:
                self.process_site()  # handle site event

        # after all points, process remaining circle events
        while not self.circles.empty():
            self.process_circle()

        self.finish_edges()

    def process_site(self):
        p = self.sites.pop()
        if not self.arc:
            self.arc = Arc(p)
            return
        # find the current arcs at p.y
        alpha = self.arc
        while alpha is not None:
            # find arc alpha which is vertically above p
            is_intersect, point_of_intersection = self.intersect(p, alpha)
            if is_intersect:
                # new parabola intersects next arc?
                is_intersect_next_arc, _ = self.intersect(p, alpha.pnext)
                if alpha.pnext and not is_intersect_next_arc:
                    # add new alpha arc between alpha and next(alpha)
                    alpha.pnext.pprev = Arc(alpha.p, point_prev=alpha, point_next=alpha.pnext)
                    alpha.pnext = alpha.pnext.pprev
                else:
                    # add at the end of the list
                    alpha.pnext = Arc(alpha.p, point_prev=alpha)
                alpha.pnext.segment_rhs = alpha.segment_rhs

                # add p between alpha and next(alpha)
                alpha.pnext.pprev = Arc(p, point_prev=alpha, point_next=alpha.pnext)
                alpha.pnext = alpha.pnext.pprev

                alpha = alpha.pnext  # now alpha points to the new arc

                # add new half-edges connected to alpha's endpoints
                seg = Segment(point_of_intersection)
                self.final_line_segments.append(seg)
                alpha.pprev.segment_rhs = alpha.segment_lhs = seg

                seg = Segment(point_of_intersection)
                self.final_line_segments.append(seg)
                alpha.pnext.segment_lhs = alpha.segment_rhs = seg

                # check for new circle events around the new arc
                self.check_circle_event(alpha, p.x)
                self.check_circle_event(alpha.pprev, p.x)
                self.check_circle_event(alpha.pnext, p.x)

                return

            alpha = alpha.pnext
        # специальный случай, при котором текущий сайт не пересекает ни одну арку выше
        alpha = self.arc
        while alpha.pnext:
            alpha = alpha.pnext
        alpha.pnext = Arc(p, point_prev=alpha)

        # insert new segment between p and i
        x = self.x0
        y = (alpha.pnext.p.y + alpha.p.y) / 2.0
        start = Point(x, y)

        seg = Segment(start)
        alpha.segment_rhs = alpha.pnext.segment_lhs = seg
        self.final_line_segments.append(seg)

    def process_circle(self):
        event = self.circles.pop()

        if event.valid:
            # start new edge
            s = Segment(event.p)
            self.final_line_segments.append(s)

            # remove associated arc (parabola)
            disappeared_arc = event.a
            if disappeared_arc.pprev is not None:
                disappeared_arc.pprev.pnext = disappeared_arc.pnext
                disappeared_arc.pprev.segment_rhs = s
            if disappeared_arc.pnext is not None:
                disappeared_arc.pnext.pprev = disappeared_arc.pprev
                disappeared_arc.pnext.segment_lhs = s

            # finish the edges before and after a
            if disappeared_arc.segment_lhs: disappeared_arc.segment_lhs.finish(event.p)
            if disappeared_arc.segment_rhs: disappeared_arc.segment_rhs.finish(event.p)

            # recheck circle events on either side of p
            if disappeared_arc.pprev: self.check_circle_event(disappeared_arc.pprev, event.x)
            if disappeared_arc.pnext: self.check_circle_event(disappeared_arc.pnext, event.x)

    # Look for a new circle event for arc i.
    def check_circle_event(self, arc, x0):
        # look for a new circle event for arc i
        # Invalidate any old event.
        self.invalidate_old_circle(arc)

        if (arc.pprev is None) or (arc.pnext is None): return

        is_breakpoints_converge, lowest_point, center_of_circle = self.circle(arc.pprev.p, arc.p, arc.pnext.p)
        if is_breakpoints_converge and (lowest_point > self.x0):
            arc.e = CircleEvent(lowest_point, center_of_circle, arc)
            self.circles.push(arc.e)

    def invalidate_old_circle(self, arc):
        if (arc.e is not None) and (arc.e.x != self.x0):
            arc.e.valid = False
        arc.e = None

    def circle(self, a, b, c):
        """магия алгебры, которую я взял из инета"""
        # check if bc is a "right turn" from ab
        if ((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) > 0: return False, None, None

        A = b.x - a.x
        B = b.y - a.y
        C = c.x - a.x
        D = c.y - a.y
        E = A * (a.x + b.x) + B * (a.y + b.y)
        F = C * (a.x + c.x) + D * (a.y + c.y)
        G = 2 * (A * (c.y - b.y) - B * (c.x - b.x))

        if (G == 0): return False, None, None  # Points are co-linear

        # point o is the center of the circle
        ox = 1.0 * (D * E - B * F) / G
        oy = 1.0 * (A * F - C * E) / G

        # o.x plus radius equals max x coord
        lowest_point = ox + math.sqrt((a.x - ox) ** 2 + (a.y - oy) ** 2)
        center_of_circle = Point(ox, oy)

        return True, lowest_point, center_of_circle

    def intersect(self, point, arc):
        """магия алгебры, которую я взял из инета"""
        # check whether a new parabola at point p intersect with arc i
        if (arc is None): return False, None
        if (arc.p.x == point.x): return False, None

        a = 0.0
        b = 0.0

        if arc.pprev is not None:
            a = (self.intersection(arc.pprev.p, arc.p, 1.0 * point.x)).y
        if arc.pnext is not None:
            b = (self.intersection(arc.p, arc.pnext.p, 1.0 * point.x)).y

        if (((arc.pprev is None) or (a <= point.y)) and ((arc.pnext is None) or (point.y <= b))):
            py = point.y
            px = 1.0 * ((arc.p.x) ** 2 + (arc.p.y - py) ** 2 - point.x ** 2) / (2 * arc.p.x - 2 * point.x)
            res = Point(px, py)
            return True, res
        return False, None

    def intersection(self, p0, p1, l):
        """магия алгебры, которую я взял из инета"""
        # get the intersection of two parabolas
        p = p0
        if (p0.x == p1.x):
            py = (p0.y + p1.y) / 2.0
        elif (p1.x == l):
            py = p1.y
        elif (p0.x == l):
            py = p0.y
            p = p1
        else:
            # use quadratic formula
            z0 = 2.0 * (p0.x - l)
            z1 = 2.0 * (p1.x - l)

            a = 1.0 / z0 - 1.0 / z1;
            b = -2.0 * (p0.y / z0 - p1.y / z1)
            c = 1.0 * (p0.y ** 2 + p0.x ** 2 - l ** 2) / z0 - 1.0 * (p1.y ** 2 + p1.x ** 2 - l ** 2) / z1

            py = 1.0 * (-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)

        px = 1.0 * (p.x ** 2 + (p.y - py) ** 2 - l ** 2) / (2 * p.x - 2 * l)
        res = Point(px, py)
        return res

    def finish_edges(self):
        l = self.x1 + (self.x1 - self.x0) + (self.y1 - self.y0)
        i = self.arc
        while i.pnext is not None:
            if i.segment_rhs is not None:
                p = self.intersection(i.p, i.pnext.p, l * 2.0)
                i.segment_rhs.finish(p)
            i = i.pnext

    def get_output(self):
        res = []
        for o in self.final_line_segments:
            p0 = o.start
            p1 = o.end
            res.append(((p0.x, p1.x), (p0.y, p1.y)))
        return res
