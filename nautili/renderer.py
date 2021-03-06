#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame

from nautili.layers import LayersHandler
from nautili import colors


class Renderer(object):
    def __init__(self, screen):
        self.screen = screen
        self._textures = []

    def add(self, obj_list):
        for obj in LayersHandler.flatten(obj_list):
            if obj:
                self._textures.append(obj)

    def clear(self):
        self._textures = []

    def update(self, obj_list=[]):
        self.clear()
        if obj_list:
            self.add(obj_list)
        self.draw()

    def fill(self, color):
        self.screen.fill(color)

    def draw(self):
        for obj in self._textures:
            self.screen.blit(obj.tile, (obj.x, obj.y))


class IsometricRenderer(Renderer):
    def __init__(self, layers_handler, screen):
        Renderer.__init__(self, screen)
        self.layers_handler = layers_handler
        self._lines = []
        self.offset = (0, 0)
        self.delta = (0, 0)

    def clear(self):
        Renderer.clear(self)
        self._lines = []

    def draw_lines(self):
        for line in self._lines:
            pygame.draw.line(self.screen, colors.RED, [line[0][0], line[0][1]], [line[1][0], line[1][1]], 2)

    def increase_offset(self, delta):
        self.offset = tuple(map(lambda x, y: x + y, self.offset, delta))
        self.delta = delta
        self.move_textures()

    def move_textures(self):
        for obj in self._textures:
            obj.rect = obj.rect.move(self.delta[0], self.delta[1])

    def draw(self):
        for obj in self._textures:
            x, y = self.layers_handler.isometric_to_orthogonal(obj.x, obj.y)
            self.screen.blit(obj.tile, (x + self.offset[0], y + self.offset[1]))
        self.draw_lines()
