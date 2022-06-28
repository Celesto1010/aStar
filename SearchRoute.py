"""
A星算法
核心在于维护两个数据结构：open集与close集。open集包含所有已搜索到的待检测节点，初始时只包含起始节点；close集包含所有已检测的节点，初始状态为空。
每个节点包含一个指向父节点的指针，以便确定追踪关系。
每个节点有G值与H值。G值代表从起始节点到该节点的移动量；H值代表该节点到目标节点移动量的估计值。
每个节点还有F值，F = G + H

算法主循环：
1. 从open集中取一个F值最小的节点（称为最优节点）；
2. 将该节点从open集中移除，加入到close集中；
3. 判断：
    3.1. 若该节点即终点，则完成并结束；
    3.2. 否则，检查该节点的所有相邻节点：
        3.2.1. 相邻节点在close集中，代表已经被检测过，无需考虑；
        3.2.2. 相邻节点在open集中，若从当前节点走到这个相邻节点所计算而得的G值更小，则更新此相邻节点的G值与F值，并重定向其父节点为当前节点
        3.2.3. 否则，将该相邻节点加入open集，设置其G值与F值，并设置其父节点为当前节点。
* 若迷宫实际不通，则在第一步时判断获取到的节点n为空，就会退出
"""
from config import MapGridType
from random import randint
from heapq import *


class TestMap(object):
    """ 简单的测试迷宫类。0代表可通行的路径单元，1代表不可通行的墙单元，2代表走过的路径 """
    def __init__(self, length, width):
        self.length = length
        self.width = width
        self.map = [[0] * self.length for _ in range(self.width)]
        self.origin_coor = 0, 0
        self.destination_coor = length - 1, width - 1

    # 随机生成若干个墙单元
    def create_block(self, block_num):
        for _ in range(block_num):
            x, y = (randint(0, self.length - 1), randint(0, self.width - 1))
            while (x, y) == self.origin_coor or (x, y) == self.destination_coor:
                x, y = (randint(0, self.length - 1), randint(0, self.width - 1))
            self.map[y][x] = MapGridType.MAP_BLOCK

    def show_map(self):
        print("+" * (3 * self.length + 2))
        for row in self.map:
            s = '+'
            for entry in row:
                s += ' ' + str(entry) + ' '
            s += '+'
            print(s)
        print("+" * (3 * self.length + 2))

    # 随机获取可移动的单元
    def generate_pos(self, range_x, range_y):
        x, y = (randint(range_x[0], range_x[1]), randint(range_y[0], range_y[1]))
        while self.map[y][x] == 1:
            x, y = (randint(range_x[0], range_x[1]), randint(range_y[0], range_y[1]))
        return x, y


class Node(object):
    """ 节点类。每个节点具有如下特征：横纵坐标、父节点、g值、f值 """
    def __init__(self, coor, g_val, h_val=0, father=None):
        self.coor = coor

        self.father = father
        self.g_val = g_val
        self.h_val = h_val
        self.f_val = 0

    def get_pos(self):
        return self.coor[0], self.coor[1]

    def get_h_val(self, dest_coor):
        return abs(dest_coor[0] - self.coor[0]) + abs(dest_coor[1] - self.coor[1])

    def reset_g_val(self, new_g_val):
        self.g_val = new_g_val
        self.reset_f_val()

    def reset_f_val(self):
        self.f_val = self.g_val + self.h_val

    def reset_father(self, father_node):
        self.father = father_node


class OpenList(object):
    """ OpenList类，基于堆，实现快速定位openList中最小F值的点. """
    def __init__(self):
        self.heap = list()
        self.open_list = dict()

    def push(self, node):
        heappush(self.heap, (node.f_val, node.coor))
        self.open_list[node.coor] = node

    def pop(self):
        node_coor = heappop(self.heap)[1]
        node = self.open_list.pop(node_coor)            # dict 移除键值对时间复杂度也是O(1)
        return node

    # 根据坐标，从open集中返回Node。若不存在则返回None
    def locate_node(self, coor):
        return self.open_list.get(coor, None)


class Astar(object):
    def __init__(self, maze):
        self.maze = maze
        self.open_list = OpenList()
        self.close_list = set()                             # close集存储的是坐标

    def search(self):
        # 建立起点终点对象，将起点加入open集
        cur_node = Node(self.maze.origin_coor, 0)                # 初始为起点
        destination = Node(self.maze.destination_coor, 0)
        self.open_list.push(cur_node)
        while True:
            # 寻找open集中f值最小的单元，并从open集中弹出。
            try:
                cur_node = self.open_list.pop()
            except IndexError:
                print(" 没有可行的路径 ")
                break
            # 若选择的单元就是终点，则结束
            if cur_node.coor == destination.coor:
                break
            # 将该单元的坐标加入到close集中
            self.close_list.add(cur_node.coor)
            # 检查该单元的相邻单元，调整open集
            self.add_adjacent_positions(cur_node)

        # 在结束后，若已经走到了终点，则依次寻找父单元，在地图上标记已经探寻过的路径单元
        while cur_node is not None:
            coor_x, coor_y = cur_node.get_pos()
            if (coor_x, coor_y) != self.maze.origin_coor and (coor_x, coor_y) != self.maze.destination_coor:
                self.maze.map[coor_y][coor_x] = MapGridType.MAP_PATH
            cur_node = cur_node.father

    def add_adjacent_positions(self, cur_node):
        # 找到当前单元的所有合法相邻单元（的坐标）
        neighbors = self.get_neighbors(cur_node.coor)
        for neighbor in neighbors:
            # 若相邻单元已经在close集中，则略过。
            if neighbor not in self.close_list:
                # 否则，检查相邻单元是否在open集中
                neighbor_node = self.open_list.locate_node(neighbor)
                # 计算这个相邻单元基于cur_node的g值
                g_val = cur_node.g_val + self.get_move_cost(cur_node, neighbor)
                # 若相邻单元不在open集中，则将其加入open集
                if neighbor_node is None:
                    node = Node(neighbor, g_val, father=cur_node)
                    node.h_val = node.get_h_val(self.maze.destination_coor)
                    node.reset_f_val()
                    self.open_list.push(node)
                # 若在open集中，且该相邻单元的原本的g值大于基于cur_node而来的g值，则更新该单元的g值为当前的g，并更新该单元的父单元
                elif neighbor_node.g_val > g_val:
                    neighbor_node.reset_g_val(g_val)
                    neighbor_node.reset_father(cur_node)

    # 判断相邻单元的坐标是否可移动。即：位于地图边界内，且不是墙单元
    def get_legal_neighbor(self, cur_coor, offset):
        new_x, new_y = (cur_coor[0] + offset[0], cur_coor[1] + offset[1])
        if new_x < 0 or new_x >= self.maze.length or \
                new_y < 0 or new_y >= self.maze.width or \
                self.maze.map[new_y][new_x] == MapGridType.MAP_BLOCK:
            return None
        return new_x, new_y

    # 定位当前单元的合法相邻单元的坐标
    def get_neighbors(self, cur_coor):
        # 定义“相邻”为周围的四个方向或八个方向
        offsets = [(-1, 0), (0, -1), (1, 0), (0, 1)]
        # offsets = [(-1,0), (0, -1), (1, 0), (0, 1), (-1,-1), (1, -1), (-1, 1), (1, 1)]
        neighbors = []
        for offset in offsets:
            neighbor = self.get_legal_neighbor(cur_coor, offset)
            if neighbor is not None:
                neighbors.append(neighbor)
        return neighbors

    # 计算移动cost。目的是区分平移还是对角移动
    @staticmethod
    def get_move_cost(cur_node, target_coor):
        if cur_node.coor[0] != target_coor[0] and cur_node.coor[1] != target_coor[1]:
            return 1.4
        return 1


if __name__ == '__main__':
    test_maze = TestMap(15, 10)
    test_maze.create_block(32)

    astar = Astar(test_maze)
    astar.maze.show_map()
    astar.search()
    astar.maze.show_map()

