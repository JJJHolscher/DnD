#
#

import pygame
import random
from random import randint
from random import seed
from copy import deepcopy
from copy import copy
from time import time
import math

pygame.init()

display_width = 800
display_height = 600

pygame.display.set_caption('Dragons & Dungeons')
clock = pygame.time.Clock()


def init():
    Screen.current = init_menu()
    init_load()
    init_new()


def main_loop():
    """"This is the main game loop."""
    run = True
    while run:
        move = [0, 0]

        for event in pygame.event.get():
            # Quit the program.
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            # Handle mouse motion events..
            elif event.type == pygame.MOUSEMOTION:

                # Drag the screen when left mouse is pressed and moves.
                if pygame.mouse.get_pressed()[0]:
                    x, y = pygame.mouse.get_rel()
                    move[0] = x
                    move[1] = y

            # Handle mouse button down events.
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                # The left mouse click begins a drag and invisible mouse.
                if pygame.mouse.get_pressed()[0]:
                    pygame.mouse.get_rel()
                    pygame.mouse.set_visible(False)

                # A right click activates the object it is pointing to.
                elif pygame.mouse.get_pressed()[2]:
                    sprite = get_sprite(x, y)
                    if sprite and sprite.action:
                        sprite.click()
                    else:
                        Screen.current.click()

                # Scrolling down zooms out.
                elif Screen.current.terrain and event.button == 4:
                    Screen.current.terrain.zoom(False, (x, y))
                    Screen.current.terrain.zoomed -= 1

                # Scrolling up zooms in.
                elif Screen.current.terrain and event.button == 5:
                    Screen.current.terrain.zoom(True, (x, y))
                    Screen.current.terrain.zoomed += 1

            # Handle mouse button up events.
            elif event.type == pygame.MOUSEBUTTONUP:
                if not pygame.mouse.get_pressed()[0]:
                    pygame.mouse.set_visible(True)

        Screen.current.move(move)
        Screen.current.draw()
        pygame.display.update()
        clock.tick(60)


class Screen:
    """Class that decides what is drawn on the display."""
    ui = dict()
    current = None
    surface = pygame.display.set_mode((display_width, display_height))

    def __init__(self, name, color, action=None):
        self.action = action
        self.background = color
        self.key = name
        self.terrain = None
        self.sprites = []

        Screen.ui[self.key] = self

    def add(self, item):
        """Add contents to the object."""
        if issubclass(type(item), Sprite):
            self.sprites.append(item)
        elif issubclass(type(item), Terrain):
            self.terrain = item
        elif type(item) == list or type(item) == tuple:
            for content in item:
                self.add(content)

    def click(self):
        """What should be done if the screen was clicked."""
        if self.action:
            self.action()

    def draw(self):
        """Draw all contents of the terrain and itself."""
        Screen.surface.fill(self.background)
        if self.terrain:
            for sprite in self.terrain.sprites:
                sprite.draw()

        for sprite in self.sprites:
            sprite.draw()

    def move(self, movement):
        """Only move sprites that are on the terrain."""
        if self.terrain:
            self.terrain.move(movement)

    def sort(self):
        """Sort the order in which sprites are drawn."""
        if self.terrain:
            self.terrain.sprites.sort(key=lambda sprite: sprite.priority)
        self.sprites.sort(key=lambda sprite: sprite.priority)


class Sprite:
    """Class for all images."""

    def __init__(self, x, y, w=0, h=0, color=(0, 0, 0)):
        self.action = None
        self.color = color
        self.priority = 0
        self.rect = pygame.Rect(x, y, w, h)
        self.surface = None
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.line = None
        self.poly = None

    def click(self):
        """Perform what the button does."""
        self.action(self)

    def draw(self):
        if self.surface:
            Screen.surface.blit(self.surface, self.rect)
        elif self.poly:
            pygame.draw.polygon(Screen.surface, self.color, self.poly)
        elif self.line:
            pygame.draw.lines(Screen.surface, self.color, False, self.line)
        else:
            pygame.draw.rect(Screen.surface, self.color, self.rect)

    def dim(self, w, h, x=None, y=None):
        if not x:
            x = self.x
        else:
            self.x = x

        if not y:
            y = self.y
        else:
            self.y = y

        self.w = w
        self.h = h

        self.rect.x = x
        self.rect.y = y
        self.rect.w = w
        self.rect.h = h

    def in_polygon(self, coord):
        """Return if a coordinate is inside the polygon."""
        inside = -1
        direction = standard_vector([coord[0] - self.x, coord[1] - self.y])
        pres = Continent.pres / 2
        new = [coord[0], coord[1]]

        while self.rect.collidepoint(new[0], new[1]):
            old = tuple(new)
            new[0] += direction[0] * pres
            new[1] += direction[1] * pres

            for i in range(len(self.poly)):
                point1 = self.poly[i]
                if i == 0:
                    point2 = self.poly[len(self.poly) - 1]
                else:
                    point2 = self.poly[i - 1]

                if intersect(old, new, point1, point2):
                    inside = inside * -1

        if inside == 1:
            return True
        return False

    def in_polygon_fast(self, coord):
        poly = []
        for point in self.poly:
            if abs(point[1] - coord[1]) < Continent.pres * 2:
                poly.append(point)

        inside = -1
        new = [coord[0], coord[1]]
        while self.x <= new[0] <= self.x + self.rect.w:
            old = [new[0], new[1]]
            new[0] += Continent.pres / 2

            for i in range(len(poly)):
                point1 = poly[i]
                if i == 0:
                    point2 = poly[len(poly) - 1]
                else:
                    point2 = poly[i - 1]

                if intersect(old, new, point1, point2):
                    inside = inside * -1

        if inside == 1:
            return True
        return False

    def text(self, string, size, font_type=None):
        """"Turn the sprite into a text box."""
        if not font_type:
            font_type = pygame.font.get_default_font()

        design = pygame.font.Font(font_type, size)
        self.surface = design.render(string, True, self.color)

        self.rect = self.surface.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


def add_points(p1, p2):
    return [p1[0] + p2[0], p1[1] + p2[1]]


def ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def circle_points(center, r, num):
    """Return a list of points that form a circle if drawn."""
    points = []
    piece = 2.0 * math.pi / float(num)
    for n in range(num):
        coord_x = center[0] + r * math.cos(piece * n)
        coord_y = center[1] + r * math.sin(piece * n)
        points.append([coord_x, coord_y])
    return points


def gen_area(points, rand=1.0, in_sprite=None):
    """Return a polygon randomly shaped around the input points."""
    rough = Sprite(0, 0)
    rough.poly = points
    rough.rect = poly_to_rect(points)

    vector = [0, 0]
    poly_points = [points[-1]]
    for i in range(len(points)):
        point = points[i]
        prev = points[index_move(i, -1, points)]
        center = [(point[0] + prev[0])/2 + 0.0001, (point[1] + prev[1])/2 + 0.1]
        side = False  # If the prev -> point line is on the south coast.
        if rough.in_polygon(center):
            side = True
        f_l = line_to_formula([prev, point])
        pointer = poly_points[-1]

        while manhattan(pointer, point) > 4 * Continent.pres:
            direction = [point[0] - pointer[0], point[1] - pointer[1]]
            direction = standard_vector(direction)
            st_vec = standard_vector(vector)
            vector = get_vector(st_vec, direction, rand)
            pointer = [poly_points[-1][0] + vector[0], poly_points[-1][1] + vector[1]]

            # We don't want the points to go too close.
            tries = 0
            while len(poly_points) > 4 and \
            shortest_distance(pointer, poly_points[:-3]) < 2 * int(Continent.pres):
                vector = get_vector(st_vec, direction, rand)
                pointer = [poly_points[-1][0] + vector[0], poly_points[-1][1] + vector[1]]
                tries += 1

                if tries > 5:
                    poly_points = poly_points[:-1]
                    break

            else:
                if (side and pointer[0] * f_l[0] + f_l[1] < pointer[1]) or\
                   (not side and pointer[0] * f_l[0] + f_l[1] > pointer[1]):
                    pointer = mirror([prev, point], pointer)

                if in_sprite and not in_sprite.in_polygon(pointer):
                    pointer = copy(get_nearest(pointer, in_sprite.poly))
                    if pointer in poly_points:
                        continue
                poly_points.append(pointer)
        poly_points.append(point)

    poly_points.extend(gen_line([poly_points[-1], points[-1]]))
    return poly_points[1:-1]


def gen_line(points, rand=1.0):
    """Generate a line that consists of multiple lines."""
    vector = [0, 0]
    lines = [list(points[0])]
    for point in points[1:]:
        pointer = lines[-1]

        while not near_point(pointer, point):
            direction = [point[0] - pointer[0], point[1] - pointer[1]]
            direction = standard_vector(direction)
            old_vector = standard_vector(vector)
            vector = get_vector(old_vector, direction, rand)
            pointer = [lines[-1][0] + vector[0], lines[-1][1] + vector[1]]

            if len(lines) < 4:
                lines.append(pointer)
                continue

            # We don't want the points to go too close.
            tries = 0
            while shortest_distance(pointer, lines[:-3]) < 2 * int(Continent.pres):
                vector = get_vector(old_vector, direction, rand)
                pointer = [lines[-1][0] + vector[0], lines[-1][1] + vector[1]]
                tries += 1
                if tries > 5:
                    lines = lines[:-1]
                    break
            else:
                lines.append(pointer)

        vector = [point[0] - pointer[0], point[1] - pointer[1]]
        lines.append(list(point))
    return lines


def get_center(points):
    """Get the central coordinates of a list of points."""
    tot_x = 0
    tot_y = 0
    for point in points:
        tot_x += point[0]
        tot_y += point[1]

    x = int(tot_x / len(points))
    y = int(tot_y / len(points))
    return x, y


def get_sprite(x, y):
    """Check for all elements in the current screen if the x and y collide
    with them."""
    for sprite in Screen.current.sprites:
        if sprite.rect.collidepoint(x, y):
            if sprite.poly and not sprite.in_polygon([x, y]):
                continue
            return sprite

    if Screen.current.terrain:
        for sprite in Screen.current.terrain.sprites:
            if sprite.rect.collidepoint(x, y):
                if sprite.poly and not sprite.in_polygon([x, y]):
                    continue
                return sprite

    return None


def get_vector(old_v, go_v, rand):
    """Make a vector that is not too fast."""
    vector = [0, 0]
    for i in range(2):
        go = []
        for j in range(-100, 100):
            new = int(old_v[i] * 100) + j

            if not -100 * Continent.pres < new < 100 * int(Continent.pres):
                continue

            num = int(200 - abs(go_v[i] * 100 - new) * rand)
            if num < 1:
                num = 0
            for _ in range(num):
                go.append(new)
        if go:
            vector[i] = int(Continent.pres * random.choice(go) / 100)
        else:
            vector[i] = go_v[i]

    return vector


def get_nearest(coord, points, same=True):
    """Return which point in the points is nearest to the coordinate."""
    nearest_point = None
    short_distance = 99999
    for point in points:
        distance = 0
        distance += abs(coord[0] - point[0])
        distance += abs(coord[1] - point[1])

        if distance < short_distance:
            if distance == 0 and not same:
                continue
            short_distance = distance
            nearest_point = point

    return nearest_point


def intersect(a, b, c, d):
    """Check if line a to b intersects with line c to d."""
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)


def index_move(current, extra, polygon):
    if current < 0 or current >= len(polygon):
        return False

    while current + extra < 0:
        extra += len(polygon)

    while current + extra >= len(polygon):
        extra -= len(polygon)

    return current + extra


def line_to_formula(line):
    """Return the a and b of a line. y = ax + b"""
    if line[1][0] == line[0][0]:
        a = 99999
    else:
        a = (line[1][1] - line[0][1]) / (line[1][0] - line[0][0])
    b = line[0][1] - line[0][0] * a
    return a, b


def manhattan(point1, point2):
    """Calculate the manhattan distance."""
    distance = abs(point1[0] - point2[0])
    distance += abs(point1[1] - point2[1])
    return distance


def mirror(line, point):
    """Get the mirror point from a point on a line."""
    a, c = line_to_formula(line)
    d = (point[0] + (point[1] - c)*a)/(1 + math.pow(a, 2))

    x = 2*d - point[0]
    y = 2*d*a - point[1] + 2 * c
    return [x, y]


def multiple_nearest(coord, obj, copy_out=False):
    """Return the point nearest to coord in a list of multiple lists"""
    if obj == []:
        return [-99999, -99999]
    elif type(obj[0][0]) is not list:
        return get_nearest(coord, obj)

    lowest = 99999
    best_point = []
    for elem in obj:
        point = multiple_nearest(coord, elem)
        score = manhattan(point, coord)
        if score < lowest:
            lowest = score
            best_point = point

    if copy_out:
        return copy(best_point)
    return best_point


def near_point(point1, point2):
    if abs(point1[0] - point2[0]) > Continent.pres:
        return False
    if abs(point1[1] - point2[1]) > Continent.pres:
        return False
    return True


def on_display(x, y):
    """Check if the given coordinates are within the window."""
    if 0 < x < display_width and 0 < y < display_height:
        return True
    return False


def passed_point(old, new, point):
    if old[0] <= point[0] < new[0]:
        return True
    if old[0] >= point[0] > new[0]:
        return True
    if old[1] <= point[1] < new[1]:
        return True
    if old[1] >= point[1] > new[1]:
        return True
    return False


def poly_to_rect(points):
    """Return a rectangle that surrounds a polygon."""
    start = points[0]
    xlow = start[0]
    xhigh = start[0]
    ylow = start[1]
    yhigh = start[1]

    for point in points[1:]:
        if point[0] < xlow:
            xlow = point[0]
        elif point[0] > xhigh:
            xhigh = point[0]
        if point[1] < ylow:
            ylow = point[1]
        elif point[1] > yhigh:
            yhigh = point[1]

    width = xhigh - xlow
    height = yhigh - ylow
    return pygame.Rect(xlow, ylow, width, height)


def pythagoras(coor1, coor2):
    return math.sqrt(sum([(a - b) ** 2 for a, b in zip(coor1, coor2)]))


def radians(v):
    """Return the angle in radians of a vector"""
    return math.atan2(v[1], v[0])


def rand_color(rmin=0, rmax=255, gmin=0, gmax=255, bmin=0, bmax=255):
    """Return random rgb values."""
    red = randint(rmin, rmax)
    blue = randint(bmin, bmax)
    green = randint(gmin, gmax)
    return [red, green, blue]


def screen_point(location, color=(255, 255, 255)):
    sprite = Sprite(0, 0)
    sprite.poly = circle_points(location, 3, 5)
    sprite.rect = poly_to_rect(sprite.poly)
    sprite.color = color
    sprite.priority = 99
    Screen.current.terrain.add(sprite)
    Screen.current.sort()


def shortest_distance(coord, points, same=False):
    """Return the shortest manhattan distance between a coord and a list."""
    shortest = 99999
    for point in points:
        if same == point:
            continue
        distance = abs(point[0] - coord[0])
        distance += abs(point[1] - coord[1])

        if distance < shortest:
            shortest = distance

    return shortest


def sort_poly(poly):
    """Sort a cloud of points into a way for a nice polygon."""
    r_to_p = dict()
    center = v_mean(poly)
    angles = []
    for point in poly:
        v = v_between_points(center, point)
        r = radians(v)
        angles.append(r)
        r_to_p[r] = point

    angles.sort()
    sorted_poly = []
    for r in angles:
        point = r_to_p[r]
        sorted_poly.append(point)
    return sorted_poly


def standard_vector(vector):
    vector_speed = pythagoras((0, 0), vector)
    if vector_speed == 0:
        return [0, 0]

    vector[0] = vector[0] / vector_speed
    vector[1] = vector[1] / vector_speed
    return vector


def v_between_points(from_point, to_point):
    """Return the vector from 'from_point' to 'to_point'"""
    return [to_point[0] - from_point[0], to_point[1] - from_point[1]]


def v_len(v):
    """Return the length of a vector"""
    square = math.pow(v[0], 2) + math.pow(v[1], 2)
    return math.sqrt(square)


def v_mean(v_list):
    """Return the average of some vectors."""
    avg_v = [0, 0]
    for v in v_list:
        avg_v[0] += v[0]
        avg_v[1] += v[1]
    return [avg_v[0]/len(v_list), avg_v[1]/len(v_list)]


def v_multiply(v, x):
    """Return a vector that is multplied by x."""
    return [v[0] * x, v[1] * x]


# Todo: Betere registratie wanneer poly2 moet worden toegevoegd.
def union(sprite1, sprite2):
    """Return a sprite that is the combination of the two input sprites."""
    poly1 = sprite1.poly
    poly2 = sprite2.poly
    new = []

    inside = sprite2.in_polygon(poly1[0])
    print(inside)
    for i in range(len(poly1)):
        point = poly1[i]

        if shortest_distance(point, poly2) > 3 * Continent.pres:
            if inside == False:
                new.append(point)
                screen_point(point)
            continue

        prev1 = poly1[index_move(i, 0, poly1)]
        next1 = poly1[index_move(i, 1, poly1)]
        for j in range(len(poly2)):
            prev2 = poly2[index_move(j, 0, poly2)]
            next2 = poly2[index_move(j, 1, poly2)]

            if intersect(prev1, next1, prev2, next2):
                if inside != False:
                    if sprite1.in_polygon(poly2[index_move(j, 1, poly2)]):
                        if sprite1.in_polygon(poly2[index_move(j, -1, poly2)]):
                            print('stres')
                        move = 1
                    else:
                        if not sprite1.in_polygon(poly2[index_move(j, -1, poly2)]):
                            print('stres')
                        move = -1

                    while inside != j:
                        new.append(poly2[inside])
                        screen_point(poly2[inside], color=(0, 0, 255))
                        inside = index_move(inside, move, poly2)
                    inside = False
                else:
                    inside = j
                break

        if inside == False:
            new.append(point)
            screen_point(point)
    new_sprite = Sprite(0, 0)
    new_sprite.poly = new
    new_sprite.rect = poly_to_rect(new)
    new_sprite.priority = -1
    return new_sprite


# -----------------------------------------------------------------------------
# --------------------------------- Culture -----------------------------------
# -----------------------------------------------------------------------------
class Culture:
    """Class for the way a civilisation represents itself."""
    pass


# -----------------------------------------------------------------------------
# ----------------------------------- Die -------------------------------------
# -----------------------------------------------------------------------------
class D:
    """Class for rolling dice."""

    def __init__(self, num1, die1, mod=0, adv=0, num2=False, die2=False,
                 num3=False, die3=False, num4=False, die4=False):
        self.num = num1
        self.die = die1
        self.mod = mod
        self.adv = adv

        if num2:
            self.num2 = num2
            self.die2 = die2
        else:
            self.num2 = 0
            self.die2 = 0

        if num2 and num3:
            self.num3 = num3
            self.die3 = die3
        else:
            self.num3 = 0
            self.die3 = 0

        if num2 and num3 and num4:
            self.num4 = num4
            self.die4 = die4
        else:
            self.num4 = 0
            self.die4 = 0

    def roll(self, mod=None, adv=None):
        """Roll your custom made die."""
        if mod is None:
            mod = self.mod
        if adv is None:
            adv = self.adv

        value = 0
        for _ in range(self.num):
            value += D.int(self.die)
        for _ in range(self.num2):
            value += D.int(self.die2)
        for _ in range(self.num3):
            value += D.int(self.die3)
        for _ in range(self.num4):
            value += D.int(self.die4)

        for _ in range(adv):
            new_value = self.roll(0, 0)
            if new_value > value:
                value = new_value

        return value + mod

    @staticmethod
    def two():
        return randint(1, 2)

    @staticmethod
    def three():
        return randint(1, 3)

    @staticmethod
    def four():
        return randint(1, 4)

    @staticmethod
    def six():
        return randint(1, 6)

    @staticmethod
    def eight():
        return randint(1, 8)

    @staticmethod
    def ten():
        return randint(1, 10)

    @staticmethod
    def twelve():
        return randint(1, 12)

    @staticmethod
    def twenty(crit=True):
        value = randint(1, 20)

        if crit and value == 1 and randint(1, 20) < 10:
            return False
        elif crit and value == 20 and randint(1, 20) > 10:
            return True
        else:
            return value

    @staticmethod
    def hundred():
        return randint(1, 100)

    @staticmethod
    def int(integer, crit=False):
        if integer == 2:
            return D.two()
        elif integer == 3:
            return D.three()
        elif integer == 4:
            return D.four()
        elif integer == 6:
            return D.six()
        elif integer == 8:
            return D.eight()
        elif integer == 10:
            return D.ten()
        elif integer == 12:
            return D.twelve()
        elif integer == 20:
            return D.twenty(crit)
        elif integer == 100:
            return D.hundred()
        return 0


# -----------------------------------------------------------------------------
# --------------------------------- Terrain -----------------------------------
# -----------------------------------------------------------------------------
class Terrain:
    """Class for everything that is done on a map."""
    all = {}

    def __init__(self, name, width, height, scale, icon=None):
        self.flavour = ''
        self.height = height
        self.icon = icon        # Terrain representation is a sprite.
        self.super = None
        self.name = name
        self.scale = scale
        self.sprites = []       # How this terrain looks.
        self.sub = {}           # All sub-terrains contained in this one.
        self.width = width
        self.zoomed = 0

        Terrain.all[name] = self

    def __repr__(self):
        return self.name + ' (Terrain)'

    def add(self, item):
        if issubclass(type(item), Sprite):
            self.sprites.append(item)

        elif issubclass(type(item), Terrain):
            self.sub[item.name] = item
            item.super = self
            self.sprites.append(item.icon)

    def move(self, movement):
        """Move all sprites of the Terrain."""
        x, y = movement

        for sprite in self.sprites:
            sprite.rect.move_ip(x, y)
            sprite.x += x
            sprite.y += y

            if sprite.poly:
                for point in sprite.poly:
                    point[0] += x
                    point[1] += y

            elif sprite.line:
                for point in sprite.line:
                    point[0] += x
                    point[1] += y

    def remove(self, item):
        self.sprites.remove(item)

    def zoom(self, zoom_in, pos):
        """Change the size and position of all sprites according to the zoom."""
        x, y = pos

        for sprite in self.sprites:
            if sprite.rect:
                small_x = sprite.x
                small_y = sprite.y
                big_x = sprite.x + sprite.w
                big_y = sprite.y + sprite.h

                if zoom_in:
                    small_x += 0.1 * (x - small_x)
                    small_y += 0.1 * (y - small_y)
                    big_x += 0.1 * (x - big_x)
                    big_y += 0.1 * (y - big_y)
                else:
                    small_x -= 0.1 * (x - small_x)
                    small_y -= 0.1 * (y - small_y)
                    big_x -= 0.1 * (x - big_x)
                    big_y -= 0.1 * (y - big_y)

                width = big_x - small_x
                height = big_y - small_y
                sprite.dim(width, height, x=small_x, y=small_y)

            if sprite.poly:
                for point in sprite.poly:
                    if zoom_in:
                        point[0] += 0.1 * (x - point[0])
                        point[1] += 0.1 * (y - point[1])
                    else:
                        point[0] -= 0.1 * (x - point[0])
                        point[1] -= 0.1 * (y - point[1])

            elif sprite.line:
                for point in sprite.line:
                    if zoom_in:
                        point[0] += 0.1 * (x - point[0])
                        point[1] += 0.1 * (y - point[1])
                    else:
                        point[0] -= 0.1 * (x - point[0])
                        point[1] -= 0.1 * (y - point[1])


class Biome(Sprite):
    """Class for all terrains sharing a similar fauna and flora."""
    types = {}

    def __init__(self, x, y, w=0, h=0, color=(0, 0, 0)):
        Sprite.__init__(self, x, y, w=w, h=h, color=color)
        self.crea = None        # Creatures, wildlife.
        self.enc = None         # Random encounters.
        self.relief = None      # If the land is flat or spiky or hills
        self.temp = None        # Temperature
        self.vega = None        # Vegetation
        self.wet = None         # Relative amount of water.


class Continent(Sprite):
    """Class for uninhabited area's."""
    pres = 7.0

    def __init__(self, x, y, w=0, h=0, color=(0, 0, 0)):
        Sprite.__init__(self, x, y, w=w, h=h, color=color)
        self.wet = 5            # Relative amount of water.
        self.biomes = []
        self.biomes_poly = []
        self.mountains = []
        self.peaks = []
        self.rivers = []

    def gen_biomes(self, width_n=3, height_n=5):
        """Generate multiple areas for biomes."""
        cats = [self.poly, self.biomes_poly, self.mountains, self.rivers]
        height = int(self.rect.height / height_n)
        width = int(self.rect.width / width_n)

        for h in range(height_n):
            for w in range(width_n):
                points = [multiple_nearest([w * width, h * height], cats, True)]
                points.append(multiple_nearest([w * width, (h + 1) * height], cats, True))
                points.append(multiple_nearest([(w + 1) * width, (h + 1) * height], cats, True))
                points.append(multiple_nearest([(w + 1) * width, h * height], cats, True))
                if points[0][0] > points[2][0] or points[0][0] > points[3][0]:
                    continue
                elif points[1][0] > points[2][0] or points[1][0] > points[3][0]:
                    continue
                elif points[0][1] > points[1][1] or points[0][1] > points[2][1]:
                    continue
                elif points[3][1] > points[1][1] or points[3][1] > points[2][1]:
                    continue

                biome = Biome(0, 0)
                biome.poly = gen_area(points, in_sprite=self)
                biome.rect = poly_to_rect(biome.poly)
                biome.color = rand_color()
                biome.priority = 999
                self.biomes.append(biome)
                self.biomes_poly.append(biome.poly)
                Screen.current.terrain.add(biome)
                Screen.current.sort()
                Screen.current.draw()
                pygame.display.update()

    def gen_mountains(self, num=70):
        """Generate mountain ranges in a continent."""
        self.priority -= 1
        self.peaks = self.local_centers(num)
        groups = Continent.grouping(self.peaks, 3.5)

        for group in groups:
            poly = Continent.mountain_group(group, self.poly)
            if len(poly) < 6:
                continue
            poly = sort_poly(poly)
            self.mountains.append(poly)
            mountain_range = Sprite(0, 0, color=rand_color())
            mountain_range.poly = gen_area(poly, in_sprite=self)
            mountain_range.rect = poly_to_rect(mountain_range.poly)
            mountain_range.priority = 5
            Screen.current.terrain.add(mountain_range)
        Screen.current.sort()
        Screen.current.draw()
        pygame.display.update()

    def gen_river(self, start, avoid=2, rand=1.0):
        """Make a river that tends to avoid mountains and merges with others."""
        vector = [0, 0]
        lines = [start]
        pointer = lines[-1]
        end = [0, 0]

        while not near_point(pointer, end):
            end = get_nearest(pointer, self.poly)
            direction = [end[0] - pointer[0], end[1] - pointer[1]]
            direction = standard_vector(direction)
            old_vector = standard_vector(vector)

            best_score = 99999
            for _ in range(avoid):
                new_vector = get_vector(old_vector, direction, rand)
                pointer = [lines[-1][0] + new_vector[0], lines[-1][1] + new_vector[1]]
                score = 99999

                for group in self.mountains:
                    nearest = shortest_distance(pointer, group)
                    if nearest < score:
                        score = nearest
                if score < best_score:
                    best_score = score
                    vector = new_vector
            pointer = [lines[-1][0] + vector[0], lines[-1][1] + vector[1]]

            if shortest_distance(pointer, self.poly) < 2 * Continent.pres:
                if not self.in_polygon(pointer):
                    lines.append(copy(get_nearest(pointer, self.poly)))
                    break

            interrupt = False
            for river in self.rivers:
                if shortest_distance(pointer, river) < 2 * Continent.pres:
                    lines.append(copy(get_nearest(pointer, river)))
                    interrupt = True
                    break
            if interrupt:
                break

            if len(lines) < 4:
                lines.append(pointer)
                continue

            # We don't want the points to go too close.
            tries = 0
            while shortest_distance(pointer, lines[:-3]) < 2 * int(
                    Continent.pres):
                vector = get_vector(old_vector, direction, rand)
                pointer = [lines[-1][0] + vector[0],
                           lines[-1][1] + vector[1]]
                tries += 1
                if tries > 5:
                    lines = lines[:-1]
                    break
            else:
                lines.append(pointer)
        else:
            lines.append(copy(end))
        return lines

    def gen_rivers(self):
        for _ in range(self.wet):
            index = randint(0, len(self.peaks) - 1)
            start = self.peaks[index]
            river = Sprite(0, 0, color=(50, 50, 255))
            river.line = self.gen_river(start)
            self.rivers.append(river.line)
            river.priority = 10
            Screen.current.terrain.add(river)
        Screen.current.sort()
        Screen.current.draw()
        pygame.display.update()

    @staticmethod
    def grouping(input_points, spread):
        """Make groups of points near each other."""
        points = deepcopy(input_points)
        groups = []

        while points:
            pointers = [points[-1]]
            new_group = []

            while pointers:
                r = pointers[-1]
                pointers.remove(r)
                new_group.append(r)

                for p in points:
                    if abs(p[0]-r[0]) < Continent.pres * spread and \
                                    abs(p[1]-r[1]) < Continent.pres * spread:
                        pointers.append(p)
                        points.remove(p)

            groups.append(new_group)
        return groups

    @staticmethod
    def line_detail(line, rand=1.0):
        new_line = []
        for i in range(1, len(line)):
            point1 = line[i - 1]
            point2 = line[i]
            new_line.extend(gen_line([point1, point2], rand=rand))

        return new_line

    def local_centers(self, num):
        centers = []
        sprites = []

        for _ in range(num):
            best_pointer = self.poly[randint(0, len(self.poly) - 1)]
            while not self.in_polygon(best_pointer):
                x_pointer = randint(self.rect.x, self.rect.x + self.rect.w)
                y_pointer = randint(self.rect.y, self.rect.y + self.rect.h)
                best_pointer = [x_pointer, y_pointer]

            longest = 0
            tries = 0
            while tries < int(0.4 * (self.rect.w + self.rect.h)):
                x_mut = 0
                y_mut = 0
                pointer = [best_pointer[0], best_pointer[1]]
                while x_mut == 0 and y_mut == 0:
                    pointer = [pointer[0] - x_mut, pointer[1] - y_mut]
                    x_mut = randint(int(-Continent.pres), int(Continent.pres + 1))
                    y_mut = randint(int(-Continent.pres), int(Continent.pres + 1))
                    pointer = [pointer[0] + x_mut, pointer[1] + y_mut]

                distance = shortest_distance(pointer, self.poly)
                if distance < 3 * int(Continent.pres):
                    if not self.in_polygon(pointer):
                        continue
                tries += 1

                if distance > longest:
                    longest = distance
                    best_pointer = [pointer[0], pointer[1]]

                    if distance > int(0.1 * (self.rect.w + self.rect.h)):
                        break

            if best_pointer not in centers:
                centers.append(best_pointer)
                mark = Sprite(0, 0, color=(0, 0, 255))
                mark.poly = circle_points(best_pointer, 2, 6)
                mark.rect = poly_to_rect(mark.poly)
                mark.priority = 99
                sprites.append(mark)
                Screen.current.terrain.add(mark)
                Screen.current.draw()
                pygame.display.update()

        for point in centers:
            if shortest_distance(point, centers) > int(Continent.pres):
                centers.remove(point)

        for mark in sprites:
            Screen.current.terrain.remove(mark)
        return centers

    @staticmethod
    def mountain_group(group, polygon):
        """Make a polygon out of a group of mountain points."""
        total_poly = []
        center = get_center(group)
        for mountain in group:
            max_radius = shortest_distance(mountain, polygon)
            radius = Continent.pres / 2

            for other in group:
                if abs(mountain[0] - other[0]) < Continent.pres * 1.5 and \
                                abs(mountain[1] - other[1]) < Continent.pres * 1.5:
                    radius = radius * 1.05

            if radius > max_radius:
                radius = max_radius

            vector = [mountain[0] - center[0], mountain[1] - center[1]]
            vector = standard_vector(vector)
            point = [mountain[0] + vector[0] * radius, mountain[1] + vector[1] * radius]

            if not total_poly:
                total_poly.append(point)
            elif shortest_distance(point, total_poly) > Continent.pres:
                total_poly.append(point)
        return total_poly


class Building(Terrain):
    """Class for all houses, shops and other constructions."""

    def __init__(self, name, width, height, scale):
        Terrain.__init__(self, name, width, height, scale)

        self.culture = None
        self.NPC = {}

    def __repr__(self):
        return self.name + " (Building)"


class Settlement(Terrain):
    """Class for all villages, cities and other urban areas."""
    all = dict()

    def __init__(self, name, width, height, scale, enc=None, size=0,
                 culture=None):
        Terrain.__init__(self, name, width, height, scale)

        self.culture = culture
        self.enc = enc
        self.NPC = {}
        self.size = size
        self.service = {}

        Settlement.all[name] = self

    def __repr__(self):
        return self.name + " (Settlement)"


# -----------------------------------------------------------------------------
# --------------------------------- Dungeon -----------------------------------
# -----------------------------------------------------------------------------
class Dungeon(Terrain):
    """Class for all dangerous areas with traps and/or encounters."""

    def __init__(self, name, width, height, scale):
        Terrain.__init__(self, name, width, height, scale)

        self.enc = None
        self.rooms = None


class Room(Terrain):
    """Class for all rooms in a building or a dungeon."""

    def __init__(self, name, width, height, scale):
        Terrain.__init__(self, width, height, scale, name)

        self.act = None         # What will happen upon entering the room.
        self.traps = None


# -----------------------------------------------------------------------------
# -------------------------------- UI screens ---------------------------------
# -----------------------------------------------------------------------------
def go_load(sprite):
    """Open the load screen."""
    Screen.current = Screen.ui['load']


def go_menu(sprite):
    """Open the menu screen."""
    Screen.current = Screen.ui['menu']


def go_new(sprite):
    """Open the screen for a new campaign."""
    Screen.current = Screen.ui['new']


def init_load():
    """Make and return a load screen."""
    load_screen = Screen('load', pygame.Color('red'))

    return load_screen


def init_menu():
    """Return the menu screen."""
    menu_screen = Screen('menu', pygame.Color('red'))

    new = Sprite(0, 0, color=pygame.Color('green'))
    new.action = go_new
    new.text('new', 60)
    new.rect.center = (display_width / 2, display_height / 3)

    load = Sprite(0, 0, color=pygame.Color('green'))
    load.action = go_load
    load.text('load', 60)
    load.rect.center = (display_width / 2, display_height * 2 / 3)

    menu_screen.add(new)
    menu_screen.add(load)
    return menu_screen


def init_new():
    """Make and return a screen for a new adventure."""
    new_screen = Screen('new', pygame.Color('purple'))
    new_terrain = Terrain('test', 0, 0, 0)
    new_screen.add(new_terrain)
    biome = Continent(200, 10)
    biome.action = test_click
    biome.poly = gen_area([[0, 0], [200, 50], [60, 400]])
    biome.rect = poly_to_rect(biome.poly)
    button = Sprite(0, 0, color=pygame.Color('white'))
    button.action = new_button
    button.text('new', 40)
    new_terrain.add(biome)
    new_screen.add(button)
    return new_screen


def new_button(sprite):
    new_screen = Screen.ui['new']
    new_terrain = new_screen.terrain

    yay = circle_points([250, 250], 200, 5)
    biome = Continent(200, 10)
    biome.poly = gen_area(yay)
    biome.rect = poly_to_rect(biome.poly)
    biome.gen_mountains()
    biome.gen_rivers()

    new_terrain.add(biome)


def test_click(sprite):
    sprite.priority -= 1
    print('Mountains:')
    sprite.gen_mountains()
    print('Rivers:')
    sprite.gen_rivers()
    print('Biomes:')
    sprite.gen_biomes()


init()
main_loop()
pygame.quit()
quit()
