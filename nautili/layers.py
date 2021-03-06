#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tiled maps handlers: read layers, objects
"""

import pygame

from nautili.models import Ship, Port, RoyalPort
from nautili.textures import Sea, Island, Rock


class LayersHandler(object):
    SEA_LAYER = 0
    DOCKS_LAYER = 1
    HIGHLIGHT_LAYER = 2
    FIRE_LAYER = 3
    ROCKS_LAYER = 4
    ISLANDS_LAYER = 5

    def __init__(self, tiledmap):
        self.tiledmap = tiledmap
        self.sea = self.get_layer_tiles(LayersHandler.SEA_LAYER, Sea)
        self.rocks = self.get_layer_tiles(LayersHandler.ROCKS_LAYER, Rock)
        self.islands = self.get_layer_tiles(LayersHandler.ISLANDS_LAYER, Island)
        self.highlighted_sea = self.get_layer_tiles(LayersHandler.HIGHLIGHT_LAYER, Sea)
        self.fire = self.get_layer_tiles(LayersHandler.FIRE_LAYER, Sea)
        self.visible_sea = LayersHandler.exclude_defined(
            LayersHandler.exclude_defined(
                self.sea,
                self.rocks),
            self.islands)
        self.shoot_obstacles = map(lambda island: island.coords(),
                                   LayersHandler.filter_not_none(LayersHandler.flatten(self.islands)))
        self.storm_move_obstacles = self.shoot_obstacles
        self.deadly_obstacles = map(lambda rock: rock.coords(),
                                    LayersHandler.filter_not_none(LayersHandler.flatten(self.rocks)))
        self.move_obstacles = self.storm_move_obstacles + self.deadly_obstacles
        self.yellow_ships = self.get_objects("ships_yellow", Ship)
        self.green_ships = self.get_objects("ships_green", Ship)
        self.ships = self.yellow_ships + self.green_ships
        self.yellow_ports = self.get_objects("ports_yellow", Port)
        self.green_ports = self.get_objects("ports_green", Port)
        self.yellow_royal_ports = self.get_objects("royal_ports_yellow", RoyalPort)
        self.green_royal_ports = self.get_objects("royal_ports_green", RoyalPort)
        self.ports = self.yellow_ports + self.green_ports
        self.royal_ports = self.yellow_royal_ports + self.green_royal_ports
        docks = self.get_layer_tiles(LayersHandler.DOCKS_LAYER, Sea)
        docks_coords = []
        for port in self.ports + self.royal_ports:
            docks_coords.extend(port.get_dock())
        for x in xrange(0, len(docks)):
            for y in xrange(0, len(docks[x])):
                if docks[x][y].coords() not in docks_coords:
                    docks[x][y] = None
        self.docks = docks
        self.docks_coords = docks_coords

    def get_layer_tiles(self, layer_num, classname):
        res = [[None for _ in xrange(0, self.tiledmap.height)] for _ in xrange(0, self.tiledmap.width)]
        for y in xrange(0, self.tiledmap.height):
            for x in xrange(0, self.tiledmap.width):
                tile = self.tiledmap.get_tile_image(x, y, layer_num)
                if tile:
                    ort_x, ort_y = self.isometric_to_orthogonal(x, y)
                    res[x][y] = classname(tile, x, y, pygame.Rect((ort_x + 16, ort_y + 30), (32, 20)))
        return res

    def get_objects(self, object_name, classname):
        res = []
        objects = filter(lambda gr: gr.name == object_name, self.tiledmap.objectgroups)[0]
        for obj in objects:
            # convert to global coords:
            player = object_name.split('_')[-1]
            res.append(classname(self, player=player, *self.tile_to_isometric(obj.x, obj.y), **obj.properties))
        return res

    def get_all_sprites(self):
        alive_ships = filter(lambda s: s.is_alive(), self.ships)
        ships_health_bars = [ship.health_bar for ship in alive_ships]
        ships_cannon_bars = [ship.cannon_bar for ship in alive_ships]
        ships_target_bars = [ship.target_bar for ship in alive_ships]
        ports_health_bars = [port.health_bar for port in self.ports]
        ports_cannon_bars = [port.cannon_bar for port in self.ports]
        ports_target_bars = [port.target_bar for port in self.ports]
        royal_ports_health_bars = [port.health_bar for port in self.royal_ports]
        return pygame.sprite.OrderedUpdates(
            sorted(alive_ships + self.ports + self.royal_ports, key=lambda s: s.x + s.y) +
            ships_health_bars + ships_cannon_bars + ships_target_bars +
            ports_health_bars + ports_cannon_bars + ports_target_bars +
            royal_ports_health_bars)

    def get_clickable_objects(self):
        return LayersHandler.filter_not_none(LayersHandler.flatten(self.visible_sea))

    def isometric_to_orthogonal(self, x, y):
        return (self.tiledmap.height + x - y - 1) * (self.tiledmap.tilewidth / 2), \
               (x + y) * (self.tiledmap.tileheight / 2)

    def get_map_polygon(self):
        p0 = self.isometric_to_orthogonal(0, 0)
        p1 = self.isometric_to_orthogonal(self.tiledmap.width, 0)
        p2 = self.isometric_to_orthogonal(self.tiledmap.width, self.tiledmap.height)
        p3 = self.isometric_to_orthogonal(0, self.tiledmap.height)
        return p0, p1, p2, p3

    def get_map_dimensions(self):
        xmax = self.isometric_to_orthogonal(self.tiledmap.width, 0)[0]
        xmin = self.isometric_to_orthogonal(0, self.tiledmap.height)[0]
        ymin = self.isometric_to_orthogonal(0, 0)[1]
        ymax = self.isometric_to_orthogonal(self.tiledmap.width, self.tiledmap.height)[1] + self.tiledmap.tileheight
        return xmax - xmin, ymax - ymin

    #def orthogonal_to_isometric(self, x, y):
    #    tw = float(self.tiledmap.tilewidth)
    #    th = float(self.tiledmap.tileheight)
    #    return x/tw + y/th + (1 - th)/2, y/th - x/tw + (th - 1)/2

    def tile_to_isometric(self, x, y):
        tw = self.tiledmap.tilewidth
        return int((2 * x) / tw) - 1, int((2 * y) / tw) + 1

    @staticmethod
    def filter_layer(layer_table, coords_list):
        res = []
        for coords in coords_list:
            try:
                res.append(layer_table[coords[0]][coords[1]])
            except IndexError:
                pass
        return res

    @staticmethod
    def exclude_defined(l1, l2):
        """
        Exclude all values from l1 that already exist in l2, e.g.
        exclude_defined([[1, 2], [3, 4]], [[None, 8], [19, None]]) -> [[1, None], [None, 4]]
        """
        return map(lambda x, y: map(lambda a, b: a if b is None else None, x, y), l1, l2)

    @staticmethod
    def filter_not_none(list):
        return filter(lambda x: x is not None, list)

    @staticmethod
    def flatten(list_of_lists):
        res = []
        for el in list_of_lists:
            if hasattr(el, "__iter__"):
                res.extend(LayersHandler.flatten(el))
            else:
                res.append(el)
        return res
