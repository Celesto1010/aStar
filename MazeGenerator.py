"""
本文件为迷宫类，包括迷宫的属性以及迷宫的生成算法
"""

from random import randint, choice
from config import MapGridType, WallDirection
from SearchRoute import Astar


class Maze(object):
    """
    地图的初始情况：外围是一圈墙，墙内为路径与墙呈格子状分布，白色单元视为路径，黑色单元视为墙。
    相邻两个白色单元之间的墙可以被去掉，视为两个路径单元相联通。
    初视的所有白色单元的坐标都是奇数（如(1, 1)、(5, 9)），则都可以表示成(2x+1, 2y+1)的形式，x、y的范围分别是大地图长宽的一半（向下取整）
    在生成迷宫时，都以xy形式定位路径单元。
    这样设计的缺点是迷宫的边界尺寸都必须是奇数。
    """
    def __init__(self, length, width, generator='backtrack', random_origin=False, random_destination=False):
        self.random_origin = random_origin
        self.random_destination = random_destination
        # 地图长宽
        self.length = length
        self.width = width
        if not generator.startswith('my'):
            if self.length % 2 != 1:
                self.length += 1
            if self.width % 2 != 1:
                self.width += 1
        # scaled尺寸即大地图长宽的一半，以此作为xy的上限，以2x+1、2y+1作为候选路径点（详见各个Generate类）
        self.scaled_length = (self.length - 1) // 2
        self.scaled_width = (self.width - 1) // 2
        # 定义生成器
        if generator == 'backtrack':
            self.generator = GeneratorRecursive(self)
        elif generator == 'cross':
            self.generator = GeneratorCross(self)
        elif generator == 'ufs':
            self.generator = GeneratorUFS(self)
        elif generator == 'mybacktrack':
            self.generator = MyGeneratorRecursive(self)
        # 起点和终点。若不用mybacktrack，则都以scaled xy表示
        self.origin = self.set_origin()
        self.destination = self.set_destination()
        # 另外存储起点和终点的实际坐标，用于a*算法自动寻路
        self.origin_coor = self.get_origin_coor()
        self.destination_coor = self.get_destination_coor()
        # 定义迷宫地图
        self.map = [[0] * self.length for _ in range(self.width)]
        # 声明a*对象
        self.astar = Astar(self)
        # 玩家游玩时当前的坐标
        self.player_loc = self.origin_coor

    # 设置图中某个格子的值
    def set_grid(self, x, y, value):
        # x代表长（横向、列），y代表宽（纵向、行），故这里设置时xy颠倒，符合嵌套列表的表示方法
        if value == MapGridType.MAP_ORIGIN:
            self.map[y][x] = 'O'
        elif value == MapGridType.MAP_DESTINATION:
            self.map[y][x] = 'D'
        elif value == MapGridType.MAP_EMPTY:
            self.map[y][x] = 0
        elif value == MapGridType.MAP_BLOCK:
            self.map[y][x] = 1
        elif value == MapGridType.MAP_PLAYER:
            self.map[y][x] = 3

    # 获得单元的属性
    def get_grid_type(self, x, y):
        if self.map[y][x] == 0:
            return MapGridType.MAP_EMPTY
        elif self.map[y][x] == 1:
            return MapGridType.MAP_BLOCK
        elif self.map[y][x] == 'O':
            return MapGridType.MAP_ORIGIN
        elif self.map[y][x] == 'D':
            return MapGridType.MAP_DESTINATION
        elif self.map[y][x] == 2:
            return MapGridType.MAP_PATH
        else:
            return MapGridType.MAP_PLAYER

    # 将图中所有单元都设成某个值
    def reset_map(self, value):
        for y in range(self.width):
            for x in range(self.length):
                self.set_grid(x, y, value)

    # 重置a*对象信息(只用在MazePlay中)
    def reset_astar(self):
        self.astar = Astar(self)

    # 设置起点
    def set_origin(self):
        if not self.random_origin:
            if not isinstance(self.generator, MyGeneratorRecursive):
                return 0, 0
            else:
                return 1, 1
        if not isinstance(self.generator, MyGeneratorRecursive):
            return randint(0, self.scaled_length - 1), randint(0, self.scaled_width - 1)
        return randint(1, self.length - 1), randint(1, self.width - 1)

    def get_origin_coor(self):
        if isinstance(self.generator, MyGeneratorRecursive):
            return self.origin
        else:
            return self.origin[0] * 2 + 1, self.origin[1] * 2 + 1

    # 设置终点
    def set_destination(self):
        if not isinstance(self.generator, MyGeneratorRecursive):
            length, width = self.scaled_length, self.scaled_width
        else:
            length, width = self.length - 1, self.width - 1
        if not self.random_destination:
            destination = length - 1, width - 1
        else:
            destination = randint(0, length - 1), randint(0, width - 1)
        while destination == self.origin:
            destination = randint(0, length - 1), randint(0, width - 1)
        return destination

    def get_destination_coor(self):
        if isinstance(self.generator, MyGeneratorRecursive):
            return self.destination
        else:
            return self.destination[0] * 2 + 1, self.destination[1] * 2 + 1

    # 判断一个单元是否合法
    def is_valid(self, x, y):
        if x < 0 or x >= self.length or y < 0 or y >= self.width:
            return False
        return True

    # 用于回溯生成法：定义每个单元是否被访问过。在生成迷宫时，初始所有的单元都是墙（1），当墙被改为路径点时，单元的值变成0，即视为已被访问过。
    def is_visited(self, x, y):
        return self.map[y][x] != 1

    # 判断一个单元是否是路径单元（是否能走），和is_visited相同
    def can_move(self, x, y):
        return self.map[y][x] != 1

    def show_map(self):
        for row in self.map:
            s = ''
            for entry in row:
                if entry == MapGridType.MAP_ORIGIN:             # 起点
                    s += ' O'
                elif entry == MapGridType.MAP_DESTINATION:      # 终点
                    s += ' D'
                elif entry == MapGridType.MAP_EMPTY:            # 空白路径
                    s += '  '
                elif entry == MapGridType.MAP_BLOCK:            # 墙
                    s += ' #'
                elif entry == MapGridType.MAP_PATH:             # a*生成路径
                    s += ' X'
                else:                                           # 玩家当前位置
                    s += ' P'
            print(s)

    def player_move(self, direction):
        init_x, init_y = self.player_loc[0], self.player_loc[1]
        direction_dict = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
        offset = direction_dict[direction]
        new_x, new_y = init_x + offset[0], init_y + offset[1]
        if self.can_move(new_x, new_y):
            if self.player_loc == self.origin_coor:
                self.set_grid(init_x, init_y, 'O')
            else:
                self.set_grid(init_x, init_y, 0)
            self.player_loc = new_x, new_y
            self.set_grid(new_x, new_y, 3)


# 迷宫生成方法1：回溯。
# 若当前单元有相邻的未访问的路径单元，则一直向这个方向搜索，直到当前单元没有未访问过的路径单元，则返回查找之前路径上未访问的单元。
# 用堆栈来维护当前访问路径上的路径单元。当堆栈变空，说明没有可访问的单元了，即迷宫创建完成。
# 1. 选择一个路径单元作为起点，加入堆栈并标记为已访问；
# 2. 当堆栈为空，终止循环；当堆栈非空，从栈顶获取一个路径单元（不出栈），进行下面的循环：
#     2.1. 若当前单元有未被访问过的相邻单元：
#         2.1.1. 随机选择一个未访问的相邻路径单元；
#         2.1.2. 去掉当前路径单元与相邻路径单元之间的墙；
#         2.1.3. 标记相邻路径单元为已访问，并将其加入堆栈。
#     2.2. 否则：
#         2.2.1. 栈顶路径单元出栈。
# https://blog.csdn.net/marble_xu/article/details/88201319?spm=1001.2014.3001.5501
class GeneratorRecursive(object):
    def __init__(self, maze):
        self.maze = maze

    def generate(self):
        # 首先将地图所有单元都设置为墙
        self.maze.reset_map(MapGridType.MAP_BLOCK)
        # 调用回溯算法
        self.recursive_backtracker()

    # 主循环的实现
    def recursive_backtracker(self):
        origin_x, origin_y = self.maze.origin
        dest_x, dest_y = self.maze.destination
        # 映射到原始地图上，确定起、终点单元的位置
        self.maze.set_grid(2 * origin_x + 1, 2 * origin_y + 1, MapGridType.MAP_ORIGIN)

        checklist = [(origin_x, origin_y)]          # checklist即为堆栈，使用缩小一半的xy来记录所有的白色单元
        while len(checklist):
            # entry = checklist[-1]                   # 取栈顶的单元/随机取栈内的一个单元
            entry_index = randint(0, len(checklist) - 1)
            entry = checklist[entry_index]
            # 检查这个单元周围是否有未被访问过的单元。若没有，则出栈
            if not self.check_adjacent_grid(entry[0], entry[1], checklist):
                # checklist.remove(entry)
                checklist.pop(entry_index)
        self.maze.set_grid(2 * dest_x + 1, 2 * dest_y + 1, MapGridType.MAP_DESTINATION)

    # 从一个单元的四周寻找未访问过的路径单元，并将其加入checklist，标记为已访问（值改成0）
    def check_adjacent_grid(self, x, y, checklist):
        # self.maze.show_map()
        # print('======================================')
        directions = []
        if x > 0:
            # 左边
            if not self.maze.is_visited(2 * (x - 1) + 1, 2 * y + 1):
                directions.append(WallDirection.WALL_LEFT)
        if y > 0:
            # 上面
            if not self.maze.is_visited(2 * x + 1, 2 * (y - 1) + 1):
                directions.append(WallDirection.WALL_UP)
        if x < self.maze.scaled_length - 1:
            # 右边
            if not self.maze.is_visited(2 * (x + 1) + 1, 2 * y + 1):
                directions.append(WallDirection.WALL_RIGHT)
        if y < self.maze.scaled_width - 1:
            # 下面
            if not self.maze.is_visited(2 * x + 1, 2 * (y + 1) + 1):
                directions.append(WallDirection.WALL_DOWN)

        # 若存在未访问过的格子：
        if len(directions):
            # 随机取一个为未访问过的单元
            direction = choice(directions)
            # 将该单元设置为MAP_EMPTY（路径），并打通这个单元与当前单元之间的墙，并将该单元加入栈
            if direction == WallDirection.WALL_LEFT:
                self.maze.set_grid(2 * (x - 1) + 1, 2 * y + 1, MapGridType.MAP_EMPTY)
                self.maze.set_grid(2 * x, 2 * y + 1, MapGridType.MAP_EMPTY)
                checklist.append((x - 1, y))
            elif direction == WallDirection.WALL_UP:
                self.maze.set_grid(2 * x + 1, 2 * (y - 1) + 1, MapGridType.MAP_EMPTY)
                self.maze.set_grid(2 * x + 1, 2 * y, MapGridType.MAP_EMPTY)
                checklist.append((x, y - 1))
            elif direction == WallDirection.WALL_RIGHT:
                self.maze.set_grid(2 * (x + 1) + 1, 2 * y + 1, MapGridType.MAP_EMPTY)
                self.maze.set_grid(2 * x + 2, 2 * y + 1, MapGridType.MAP_EMPTY)
                checklist.append((x + 1, y))
            elif direction == WallDirection.WALL_DOWN:
                self.maze.set_grid(2 * x + 1, 2 * (y + 1) + 1, MapGridType.MAP_EMPTY)
                self.maze.set_grid(2 * x + 1, 2 * y + 2, MapGridType.MAP_EMPTY)
                checklist.append((x, y + 1))
            return True
        else:
            return False


class MyGeneratorRecursive(object):
    """ 不用xy映射法生成的迷宫。缺点是会产生四周不相连的墙面 """
    def __init__(self, maze):
        self.maze = maze

    def generate(self):
        # 首先将地图所有单元都设置为墙
        self.maze.reset_map(MapGridType.MAP_BLOCK)
        # 调用回溯算法
        self.recursive_backtracker()

    def recursive_backtracker(self):
        origin_x, origin_y = self.maze.origin
        dest_x, dest_y = self.maze.destination
        # 映射到原始地图上，确定起点单元的位置
        self.maze.set_grid(origin_x, origin_y, MapGridType.MAP_ORIGIN)

        checklist = [(origin_x, origin_y)]          # checklist即为堆栈，使用缩小一半的xy来记录所有的白色单元
        while len(checklist):
            # entry = checklist[-1]                   # 取栈顶的单元/随机取栈内的一个单元
            entry_index = randint(0, len(checklist) - 1)
            entry = checklist[entry_index]
            # 检查这个单元周围是否有未被访问过的单元。若没有，则出栈
            if not self.check_adjacent_grid(entry[0], entry[1], checklist):
                # checklist.remove(entry)
                checklist.pop(entry_index)
        self.maze.set_grid(dest_x, dest_y, MapGridType.MAP_DESTINATION)

    # 从一个节点的四周寻找未访问过的节点，并将其加入checklist，标记为已访问（值改成0）
    # 加入额外的限制：相邻的未访问的点，若其周围已经有另外的已访问的点，则不做访问
    def check_adjacent_grid(self, x, y, checklist):
        directions = []
        if x > 1:
            # 左边
            if not self.maze.is_visited(x - 1, y) and \
                    not self.maze.is_visited(x - 2, y) and \
                    not self.maze.is_visited(x - 1, y + 1) and \
                    not self.maze.is_visited(x - 1, y - 1):
                directions.append(WallDirection.WALL_LEFT)
        if y > 1:
            # 上面
            if not self.maze.is_visited(x, y - 1) and \
                    not self.maze.is_visited(x, y - 2) and \
                    not self.maze.is_visited(x - 1, y - 1) and \
                    not self.maze.is_visited(x + 1, y - 1):
                directions.append(WallDirection.WALL_UP)
        if x < self.maze.length - 2:
            # 右边
            if not self.maze.is_visited(x + 1, y) and \
                    not self.maze.is_visited(x + 2, y) and \
                    not self.maze.is_visited(x + 1, y - 1) and \
                    not self.maze.is_visited(x + 1, y + 1):
                directions.append(WallDirection.WALL_RIGHT)
        if y < self.maze.width - 2:
            # 下面
            if not self.maze.is_visited(x, y + 1) and \
                    not self.maze.is_visited(x, y + 2) and \
                    not self.maze.is_visited(x - 1, y + 1) and \
                    not self.maze.is_visited(x + 1, y + 1):
                directions.append(WallDirection.WALL_DOWN)

        # 若存在未访问过的格子：
        if len(directions):
            # 随机取一个为未访问过的格子
            direction = choice(directions)
            if direction == WallDirection.WALL_LEFT:
                self.maze.set_grid(x - 1, y, MapGridType.MAP_EMPTY)
                checklist.append((x - 1, y))
            elif direction == WallDirection.WALL_UP:
                self.maze.set_grid(x, y - 1, MapGridType.MAP_EMPTY)
                checklist.append((x, y - 1))
            elif direction == WallDirection.WALL_RIGHT:
                self.maze.set_grid(x + 1, y, MapGridType.MAP_EMPTY)
                checklist.append((x + 1, y))
            elif direction == WallDirection.WALL_DOWN:
                self.maze.set_grid(x, y + 1, MapGridType.MAP_EMPTY)
                checklist.append((x, y + 1))
            return True
        else:
            return False


# 迷宫生成算法2：递归分割算法
# 本算法所基于的地图基本与回溯算法类似，只是初视状态变成外围一圈墙单元，内部全部都是路径单元。
# 用一个十字的墙单元将地图分成四块，该十字的交点标记为(wall_x, wall_y)。若按照上述的xy标记路径方法，这里wall_x, wall_y的原始坐标都必须是偶数
# 随后，在这四块的相交的四条边中随机选择三条边打通（即每条边去掉一个墙单元），使得这四块相连通
# 在这四块中持续建立十字的墙单元，进行递归，直到某一块的长或宽≤1（即无法再建立十字）
# 1. 确定一个矩阵块
# 2. 判断矩阵块是否能继续分割
#     2.1. 若能继续分割：
#         2.1.1. 随机选择矩阵块内的十字交点的位置，将矩阵块内这条十字上的所有单元都设为墙，分成四个更小的矩阵块
#         2.1.2. 十字的四个边，随机选择三个，这三个边随机选择一个墙单元，将其打通成路径单元
#         2.1.3. 对四个小矩阵块继续递归
#     2.2. 不能继续分割，返回
class GeneratorCross(object):
    """ 缺点是可能会生成含有多个很长的直路的迷宫 """
    def __init__(self, maze):
        self.maze = maze

    def generate(self):
        # 首先将四周都设置为墙
        for x in range(0, self.maze.length):
            self.maze.set_grid(x, 0, MapGridType.MAP_BLOCK)
            self.maze.set_grid(x, self.maze.width - 1, MapGridType.MAP_BLOCK)
        for y in range(0, self.maze.width):
            self.maze.set_grid(0, y, MapGridType.MAP_BLOCK)
            self.maze.set_grid(self.maze.length - 1, y, MapGridType.MAP_BLOCK)

        # 标记起点终点
        origin_x, origin_y = self.maze.origin
        dest_x, dest_y = self.maze.destination
        # 映射到原始地图上，确定起、终点单元的位置
        self.maze.set_grid(2 * origin_x + 1, 2 * origin_y + 1, MapGridType.MAP_ORIGIN)

        # 执行递归。
        # 初始基准点为最左上角的路径单元。基准点即矩形块的左上角路径单元的坐标
        # 初视十字的长、宽即地图的长、宽-2（排除两个边缘的墙单元）
        self.recursive_division(1, 1, self.maze.length - 2, self.maze.width - 2)
        self.maze.set_grid(2 * dest_x + 1, 2 * dest_y + 1, MapGridType.MAP_DESTINATION)

    def recursive_division(self, base_x, base_y, rec_length, rec_width):
        # self.maze.show_map()
        # print()
        # 递归终止条件：矩形块的长或宽≤1
        if rec_length <= 1 or rec_width <= 1:
            return

        # 确定十字墙的交点坐标。其坐标必须都是偶数
        wall_x, wall_y = (self.get_wall_index(base_x, rec_length), self.get_wall_index(base_y, rec_width))

        # 生成这个矩形块内的十字墙单元
        for i in range(base_x, base_x + rec_length):
            self.maze.set_grid(i, wall_y, MapGridType.MAP_BLOCK)
        for i in range(base_y, base_y + rec_width):
            self.maze.set_grid(wall_x, i, MapGridType.MAP_BLOCK)

        # 在十字墙的四个边中随机打通三个墙单元
        self.generate_holes(base_x, base_y, rec_length, rec_width, wall_x, wall_y)

        # 在四个子矩形块内继续，顺序分别是左上、左下、右上、右下
        self.recursive_division(base_x, base_y, wall_x - base_x, wall_y - base_y)
        self.recursive_division(base_x, wall_y + 1, wall_x - base_x, base_y + rec_width - wall_y - 1)
        self.recursive_division(wall_x + 1, base_y, base_x + rec_length - wall_x - 1, wall_y - base_y)
        self.recursive_division(wall_x + 1, wall_y + 1, base_x + rec_length - wall_x - 1, base_y + rec_width - wall_y - 1)

    @staticmethod
    def get_wall_index(start, length):
        assert length >= 3              # 尺寸大于3才能生成十字
        wall_index = randint(start + 1, start + length - 2)         # 在矩形块方向范围内随机取一个点
        if wall_index % 2 == 1:                                     # 保证是偶数
            wall_index -= 1
        return wall_index

    # 在打通随机墙单元时，需要检查十字与矩形块的交点。
    # 若交点已经是路径单元了（先前已被打通），则直接打通交点之前的边缘单元，否则会导致迷宫不连通。
    def generate_holes(self, base_x, base_y, rec_length, rec_width, wall_x, wall_y):
        holes = []
        # 在十字的四个边分别随机取一个点
        hole_entries = [
            (randint(base_x, wall_x - 1), wall_y),                      # 十字左墙随机取一个点
            (randint(wall_x + 1, base_x + rec_length - 1), wall_y),     # 十字右墙随机取一个点
            (wall_x, randint(base_y, wall_y - 1)),                      # 十字上墙随机取一个点
            (wall_x, randint(wall_y + 1, base_y + rec_width - 1))       # 十字下墙随机取一个点
        ]
        # 十字的四个即将与矩形块的边界相交的边缘点的坐标
        margin_entries = [
            (base_x, wall_y),                       # 左边
            (base_x + rec_length - 1, wall_y),      # 右边
            (wall_x, base_y),                       # 上边
            (wall_x, base_y + rec_width - 1)        # 下边
        ]
        # 十字的四个与矩形块的边界相交的端点的坐标
        adjacent_entries = [
            (base_x - 1, wall_y),                   # 左边
            (base_x + rec_length, wall_y),          # 右边
            (wall_x, base_y - 1),                   # 上边
            (wall_x, base_y + rec_width)            # 下边
        ]
        # 遍历十字的四个方向
        for i in range(4):
            adj_x, adj_y = (adjacent_entries[i][0], adjacent_entries[i][1])
            # 若交点合法且交点已经是路径单元了，则直接打通对应方向的边缘位置为路径单元
            if self.maze.is_valid(adj_x, adj_y) and self.maze.can_move(adj_x, adj_y):
                self.maze.set_grid(margin_entries[i][0], margin_entries[i][1], MapGridType.MAP_EMPTY)
            # 否则，记录十字的对应方向的边所取的打通的位置
            else:
                holes.append(hole_entries[i])
        # 随机取holes进行打通
        ignore_hole = randint(0, len(holes) - 1)
        for i in range(0, len(holes)):
            if i != ignore_hole:
                self.maze.set_grid(holes[i][0], holes[i][1], MapGridType.MAP_EMPTY)


# 迷宫生成算法3：生成树＋并查集
# 基本的生成树Kruskal算法：
# 1. 将每个点作为一个单独的树，并选择好起点和终点；
# 2. 循环：随机选择一条边，判断边连接的顶点是否在同一子树中。
#     2.1. 若不在，则连通这两个顶点，即将这两个顶点置于同一颗子树中；
#     2.2. 若在，则判断起终点是否在同一子树中。若也在，则表示已经生成好了一棵树，退出循环
# 这种算法中，图的边可以视为迷宫的墙单元，连接两个顶点生成边可以视为生成一段墙单元。
# 为避免同时记录路径单元和墙单元，采用改进版本，只维护一个路径单元列表，视路径单元为图的顶点判断路径单元和其相邻的路径单元是否在同一颗子树中。
# 当完成一棵树，代表生成了完整路径的迷宫。
# 算法逻辑：
# 1. 将每个路径单元都初始化为一颗单独的树，同时加入检查列表
# 2. 循环：当检查列表非空，随机从列表中取出一个路径单元，检查该单元与其相邻的路径单元是否同属一颗树。
#     2.1. 有相邻的路径单元与其不属于同一棵树，则随机选择一个这样的相邻路径单元，将该单元与当前单元合并成一棵树（使用并查集）
#     2.2. 否则，表示当前路径单元与其所有相邻路径单元都属于同一棵树，从检查列表中删除该路径单元
# 并查集的应用方法：
# 1. 存储。每棵树都有唯一的根节点，用这个根节点来代表这棵树的所有节点所在的合集
#     初始化：每个节点(x, y)看作一棵树，自己就是这棵树的根节点，将自己的坐标作为自己这个合集的标识；
#     查询：对于节点(x, y)，通过节点不断查找其父节点，直到找到根节点。
# 2. 判断两个节点是否属于同一棵树：找到这两个节点所在树的根节点，判断两个根节点是否相同。
# 3. 合并。
#     每棵树的根节点存储一个属性weight，表示这棵树拥有的子节点数——节点较多的称作大树，较少的称作小树。合并时，保证小树变成大树的子树。
class GeneratorUFS(object):
    def __init__(self, maze):
        self.maze = maze
        # 用一个长度为路径单元总和的列表记录父节点
        # parent_list存储每个路径单元的父节点。初始化时即路径单元自己
        self.parent_list = [x for x in range(self.maze.scaled_length * self.maze.scaled_width)]
        # weight_list为每个迷宫单元的权重，初始化时为1
        self.weight_list = [1 for _ in range(self.maze.scaled_length * self.maze.scaled_width)]

    def generate(self):
        # 首先将所有单元都设为墙
        self.maze.reset_map(MapGridType.MAP_BLOCK)
        # 标记起点终点
        origin_x, origin_y = self.maze.origin
        dest_x, dest_y = self.maze.destination
        # 执行并查集生成迷宫
        self.union_find_set()
        # 映射到原始地图上，确定起、终点单元的位置
        self.maze.set_grid(2 * origin_x + 1, 2 * origin_y + 1, MapGridType.MAP_ORIGIN)
        self.maze.set_grid(2 * dest_x + 1, 2 * dest_y + 1, MapGridType.MAP_DESTINATION)

    def union_find_set(self):
        checklist = list()
        for x in range(self.maze.scaled_length):
            for y in range(self.maze.scaled_width):
                checklist.append((x, y))
                self.maze.set_grid(2 * x + 1, 2 * y + 1, MapGridType.MAP_EMPTY)
        while checklist:
            entry = choice(checklist)
            if not self.check_adjacent_pos(entry[0], entry[1]):
                checklist.remove(entry)

    # 确定路径单元的树节点的index
    def get_node_index(self, x, y):
        return x * self.maze.scaled_width + y

    # 已知路径单元的树节点的index，寻找其根节点的index
    def find_root(self, index):
        if index != self.parent_list[index]:
            return self.find_root(self.parent_list[index])        # 一层一层寻找父节点
        return self.parent_list[index]

    # 合并两棵树。index即为两个节点
    def union(self, index1, index2):
        # 寻找两个节点的根节点(的index)
        root1 = self.find_root(index1)
        root2 = self.find_root(index2)
        # 若两个根节点相同，则无需合并
        if root1 == root2:
            return
        else:
            # 将较小的树合并到较大的树中，即指定较小树的根节点的父节点为较大树的根节点
            if self.weight_list[root1] > self.weight_list[root2]:
                self.parent_list[root2] = root1
                self.weight_list[root1] += self.weight_list[root2]
            else:
                self.parent_list[root1] = root2
                self.weight_list[root2] += self.weight_list[root1]

    # 检查一个路径单元相邻的四个路径单元
    def check_adjacent_pos(self, x, y):
        # self.maze.show_map()
        # print('-----------------------')
        directions = []
        # 定位到这个路径单元的index与其根节点的index
        node1 = self.get_node_index(x, y)
        root1 = self.find_root(node1)
        if x > 0:
            root2 = self.find_root(self.get_node_index(x - 1, y))
            if root1 != root2:
                directions.append(WallDirection.WALL_LEFT)
        if y > 0:
            root2 = self.find_root(self.get_node_index(x, y - 1))
            if root1 != root2:
                directions.append(WallDirection.WALL_UP)
        if x < self.maze.scaled_length - 1:
            root2 = self.find_root(self.get_node_index(x + 1, y))
            if root1 != root2:
                directions.append(WallDirection.WALL_RIGHT)
        if y < self.maze.scaled_width - 1:
            root2 = self.find_root(self.get_node_index(x, y + 1))
            if root1 != root2:
                directions.append(WallDirection.WALL_DOWN)

        if len(directions):
            direction = choice(directions)
            if direction == WallDirection.WALL_LEFT:
                adj_x, adj_y = (x - 1, y)
                self.maze.set_grid(2 * x, 2 * y + 1, MapGridType.MAP_EMPTY)
            elif direction == WallDirection.WALL_UP:
                adj_x, adj_y = (x, y - 1)
                self.maze.set_grid(2 * x + 1, 2 * y, MapGridType.MAP_EMPTY)
            elif direction == WallDirection.WALL_RIGHT:
                adj_x, adj_y = (x + 1, y)
                self.maze.set_grid(2 * x + 2, 2 * y + 1, MapGridType.MAP_EMPTY)
            else:
                adj_x, adj_y = (x, y + 1)
                self.maze.set_grid(2 * x + 1, 2 * y + 2, MapGridType.MAP_EMPTY)
            node2 = self.get_node_index(adj_x, adj_y)
            self.union(node1, node2)
            return True
        else:
            return False


def play(maze):
    while True:
        d = input()
        maze.player_move(d)
        maze.show_map()
        if maze.destination_coor == maze.player_loc:
            print('CONGRATULATIONS!')
            break


if __name__ == '__main__':
    the_maze = Maze(
        length=11,
        width=11,
        generator='ufs',
        random_origin=True,
        random_destination=True
    )
    the_maze.generator.generate()
    the_maze.show_map()
    # print()
    # the_maze.astar.search()
    # the_maze.show_map()
    play(the_maze)

