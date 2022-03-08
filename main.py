import random


class Position:
    _x = None
    _y = None

    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def __str__(self):
        return f"Position({self.x}, {self.y})"

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))

    @staticmethod
    def position_range(n, m=None):
        if m is None:
            m = n
        for i in range(1, n+1):
            for j in range(1, m+1):
                yield Position(i, j)


class CellInfo:
    _ship = None
    _is_hit = False

    @property
    def ship(self):
        return self._ship

    @ship.setter
    def ship(self, value):
        self._ship = int(value)

    @property
    def is_hit(self):
        return self._is_hit

    def hit(self):
        self._is_hit = True

    def __str__(self):
        return 'O' if not self.is_hit and self.ship is None else \
               'T' if self.is_hit and self.ship is None else \
               '■' if not self.is_hit else \
               'X'


class Ship:
    _head = None
    _length = 0
    _direction = 0
    _hit_points = 0

    def __init__(self, length, head, direction):
        self._head = head
        self._length = length
        self._direction = direction
        self._hit_points = length

    @property
    def head(self):
        return self._head

    @property
    def length(self):
        return self._length

    @property
    def direction(self):
        return self._direction

    @property
    def hit_points(self):
        return self._hit_points

    def hit(self):
        self._hit_points -= 1
        return not self.hit_points

    @property
    def position(self):
        if self.direction:
            position_list = [Position(self.head.x + i, self.head.y) for i in range(self.length)]
        else:
            position_list = [Position(self.head.x, self.head.y + i) for i in range(self.length)]
        return position_list

    @property
    def contour(self):
        if self.direction:
            position_list = [Position(self.head.x + i, self.head.y - 1) for i in range(-1, self.length+1)]
            position_list.append(Position(self.head.x + self.length, self.head.y))
            position_list.extend(Position(self.head.x + i, self.head.y + 1) for i in range(self.length, -2, -1))
            position_list.append(Position(self.head.x - 1, self.head.y))
        else:
            position_list = [Position(self.head.x - 1, self.head.y + i) for i in range(-1, self.length+1)]
            position_list.append(Position(self.head.x, self.head.y + self.length))
            position_list.extend(Position(self.head.x + 1, self.head.y + i) for i in range(self.length, -2, -1))
            position_list.append(Position(self.head.x, self.head.y - 1))
        return position_list


class Field:
    _size = 0
    _alive_ships = 0
    _ships = None
    _cells = None

    def __init__(self, size=6):
        self._size = size
        self._cells = {pos: CellInfo() for pos in Position.position_range(size)}
        self._ships = []

    @property
    def size(self):
        return self._size

    @property
    def alive_ships(self):
        return self._alive_ships

    @property
    def cells(self):
        return self._cells.copy()

    def get_cell_info(self, pos):
        return self._cells[pos]

    def get_ship_info(self, num):
        return self._ships[num]

    def can_add_ship(self, ship):
        return not any([self.is_locked(pos) for pos in ship.position])

    def can_add_ship_list(self, length):
        position_list = [(cell, direction) for cell in self.cells.keys() for direction in (0, 1)]
        return list(filter(lambda position: self.can_add_ship(Ship(length, *position)), position_list))

    def add_ship(self, length, head, direction):
        if direction not in range(2):
            raise ValueError('Направелние должно быть 0 (вправо) или 1 (вниз)')

        new_ship = Ship(length, head, direction)

        if not self.can_add_ship(new_ship):
            raise ValueError('Невозможно разместить корабль с данными параметрами')

        self._ships.append(new_ship)
        for pos in new_ship.position:
            self._cells[pos].ship = self.alive_ships
        self._alive_ships += 1

    def is_inside(self, pos):
        return pos in self.cells

    def is_ship(self, pos):
        if not self.is_inside(pos):
            return False
        return self.get_cell_info(pos).ship is not None

    #Проверяет возможность поставить корабль в клетку (True-нельзя поставить)
    def is_locked(self, pos):
        if not self.is_inside(pos):
            return True
        position_list = [Position(pos.x+i, pos.y+j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
        return any([self.is_ship(position) for position in position_list])

    def _set_hit(self, pos):
        self._cells[pos].hit()
        ship_num = self.get_cell_info(pos).ship
        if ship_num is not None: #Проверяем попадение в корабль
            if self._ships[ship_num].hit(): #Проверяем уничтожение коробля
                for position in self.get_ship_info(ship_num).contour:
                    if self.is_inside(position):
                        self._set_hit(position)
                self._alive_ships -= 1
            return True
        return False

    def shoot(self, pos):
        if not self.is_inside(pos):
            raise ValueError('Совсем мимо')
        if self.get_cell_info(pos).is_hit:
            raise ValueError('Сюда нельзя стрелять')
        return self._set_hit(pos)

    def __str__(self):
        cells = self.cells
        field_str = [' | '.join([str(cells[Position(i, j)]) for j in range(1, self.size+1)]) for i in range(1, self.size+1)]
        field_str = '\n'.join([f'{i+1} | {field_str[i]} |' for i in range(self.size)])
        field_str = '  | ' + ' | '.join(map(str, range(1, self.size+1))) + ' |\n' + field_str
        return field_str

    def to_str(self, hid=False):
        field_str = str(self)
        if hid:
            field_str = field_str.replace('■', 'O')
        return field_str

    @property
    def can_shoot_list(self):
        cells = self.cells
        return list(filter(lambda position: not cells[position].is_hit, cells.keys()))


class Player(Field):
    def __init__(self, field_size, ship_list):
        super().__init__(field_size)
        for ship_length in ship_list:
            self.player_add_ship(ship_length)

    def player_add_ship(self, length):
        if not self.can_add_ship_list(length):
            raise GameException('На поле нельзя поставить корабль такой длины')
        while True:
            try:
                inp = input(f'Введите координаты и направление (0 - вправо, 1 - вниз) для {length}-палубного коробля:\n')
                inp = list(map(int, inp.split()))
                if len(inp) != 3:
                    raise ValueError('Должно быть 3 числа.')
                self.add_ship(length, Position(inp[0], inp[1]), inp[2])
            except ValueError as e:
                print('Что-то пошло не так:', e)
            else:
                print('Корабль добавлен. Ваше поле:')
                print(self.to_str())
                return

    @staticmethod
    def player_make_shoot(other):
        while True:
            try:
                print('Поле противника:')
                print(other.to_str(True))
                inp = input('Введите координаты для выстерла:\n')
                inp = list(map(int, inp.split()))
                if len(inp) != 2:
                    raise ValueError('Должно быть 2 числа.')
                hit = other.shoot(Position(*inp))
            except ValueError as e:
                print('Что-то пошло не так:', e)
            else:
                print('Попадание!.') if hit else print('Мимо.')
                return hit

    def shoot(self, pos):
        hit = super().shoot(pos)
        print('По вашему кораблю попали. Ваше поле:') if hit else print('По вам пальнули, но промазали. Ваше поле:')
        print(self.to_str())
        return hit


class AIPlayer(Field):
    def __init__(self, field_size, ship_list):
        super().__init__(field_size)
        for ship_length in ship_list:
            self.player_add_ship(ship_length)

    def player_add_ship(self, length):
        position_list = self.can_add_ship_list(length)
        if not position_list:
            raise GameException('ИИ накасячил с рамещением кораблей')
        position = random.choice(position_list)
        self.add_ship(length, *position)

    @staticmethod
    def player_make_shoot(other):
        position = random.choice(other.can_shoot_list)
        return other.shoot(position)


class GameException(Exception):
    pass


class Game:
    _player_one = None
    _player_two = None

    def __init__(self, field_size=6, ship_list=(3, 2, 2, 1, 1, 1, 1)):
        while True:
            try:
                self._player_one = Player(field_size, ship_list)
            except GameException as e:
                print('Что-то пошло не так:', e)
            else:
                break
        while True:
            try:
                self._player_two = AIPlayer(field_size, ship_list)
            except GameException:
                pass
            else:
                break
        if self.start_game():
            print('Игрок победил')
        else:
            print('Игрок проиграл')

    def start_game(self):
        while True:
            while self._player_one.player_make_shoot(self._player_two):
                if not self._player_two.alive_ships:
                    return True
            while self._player_two.player_make_shoot(self._player_one):
                if not self._player_one.alive_ships:
                    return False


if __name__ == '__main__':
    Game()
