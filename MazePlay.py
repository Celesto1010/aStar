import pygame
from sys import exit

from MazeGenerator import Maze, MapGridType


# 迷宫尺寸
REC_SIZE = 10                               # 单元尺寸
REC_LENGTH = 61                             # 迷宫长度
REC_WIDTH = 61                              # 迷宫宽度
BUTTON_LENGTH = 120                         # 按钮长度
BUTTON_WIDTH = 30                           # 按钮宽度
SCREEN_LENGTH = REC_LENGTH * REC_SIZE       # 屏幕长度
SCREEN_WIDTH = REC_WIDTH * REC_SIZE + BUTTON_WIDTH      # 屏幕宽度

RANDOM_ORIGIN = False
RANDOM_DESTINATION = False


class Button(object):
    def __init__(self, screen, generator, x, y):
        self.screen = screen
        self.length = BUTTON_LENGTH
        self.width = BUTTON_WIDTH
        self.button_color = (128, 128, 128)
        self.text_color = [(0, 255, 0), (255, 0, 0)]
        self.font = pygame.font.SysFont('name', BUTTON_WIDTH * 2 // 3)

        self.rect = pygame.Rect(0, 0, self.length, self.width)
        self.rect.topleft = (x, y)
        self.generator = generator

        # 初始化
        self.msg_image = self.font.render(self.generator, True, self.text_color[0], self.button_color)
        self.msg_image_rect = self.msg_image.get_rect()
        self.msg_image_rect.center = self.rect.center

    def draw(self):
        self.screen.fill(self.button_color, self.rect)
        self.screen.blit(self.msg_image, self.msg_image_rect)

    def click(self, game):
        game.maze_generator = self.generator.lower()
        self.msg_image = self.font.render(self.generator, True, self.text_color[1], self.button_color)

    def unclick(self):
        self.msg_image = self.font.render(self.generator, True, self.text_color[0], self.button_color)


class Game(object):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode([SCREEN_LENGTH, SCREEN_WIDTH])
        self.clock = pygame.time.Clock()
        self.maze_generator = 'cross'
        self.maze = Maze(REC_LENGTH, REC_WIDTH, self.maze_generator)
        self.mode = 0
        self.buttons = []
        self.buttons.append(Button(self.screen, 'BACKTRACK', 0, 0))
        self.buttons.append(Button(self.screen, 'CROSS', BUTTON_WIDTH + 80, 0))
        self.buttons.append(Button(self.screen, 'UFS', (BUTTON_WIDTH + 80) * 2, 0))
        self.buttons.append(Button(self.screen, 'MyBACKTRACK', (BUTTON_WIDTH + 80) * 3, 0))
        self.buttons[1].click(self)

    def play(self):
        self.clock.tick(30)

        pygame.draw.rect(self.screen, (255, 255, 255), pygame.Rect(0, 0, SCREEN_WIDTH, BUTTON_WIDTH))
        for button in self.buttons:
            button.draw()

        for y in range(self.maze.width):
            for x in range(self.maze.length):
                grid_type = self.maze.get_grid_type(x, y)
                if grid_type == MapGridType.MAP_EMPTY:
                    color = (255, 255, 255)                 # 白，代表路径
                elif grid_type == MapGridType.MAP_BLOCK:
                    color = (0, 0, 0)                       # 黑，代表墙
                elif grid_type == MapGridType.MAP_PATH:
                    color = (135, 206, 235)                 # 天蓝，代表a*自动寻路的路径
                elif grid_type == MapGridType.MAP_DESTINATION:
                    color = (255, 0, 0)                     # 红，代表终点
                elif grid_type == MapGridType.MAP_ORIGIN:
                    color = (0, 255, 0)                     # 绿，代表起点
                else:
                    color = (255, 255, 0)                   # 黄，代表玩家游玩当前的位置（功能开发中）
                pygame.draw.rect(self.screen, color,
                                 pygame.Rect(REC_SIZE * x, REC_SIZE * y + BUTTON_WIDTH, REC_SIZE, REC_SIZE))

    def generate_maze(self):
        if self.mode >= 2:
            self.mode = 0
        if self.mode == 0:
            self.reset_maze()
            self.maze.generator.generate()
        elif self.mode == 1:
            self.maze.astar.search()
        else:
            self.maze.reset_map(MapGridType.MAP_EMPTY)
            self.maze.reset_astar()
        self.mode += 1

    def reset_maze(self):
        self.maze = Maze(REC_LENGTH, REC_WIDTH, self.maze_generator, RANDOM_ORIGIN, RANDOM_DESTINATION)


def check_buttons(game, mousex, mousey):
    for button in game.buttons:
        if button.rect.collidepoint(mousex, mousey):
            button.click(game)
            for tmp in game.buttons:
                if tmp != button:
                    tmp.unclick()
            break


def play(game, k_button):
    ...


if __name__ == '__main__':
    the_game = Game()
    while True:
        the_game.play()
        pygame.display.update()

        for event in pygame.event.get():
            # 退出
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                the_game.generate_maze()
                break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                check_buttons(the_game, mouse_x, mouse_y)