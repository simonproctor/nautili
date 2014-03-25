#!/usr/bin/env python
__author__ = 'aikikode'

import pygame
import random
from pytmx import tmxloader
from hud import Button
from renderer import Renderer, IsometricRenderer
from layers import LayersHandler
from settings import PLAYER1, PLAYER2, DISPLAY, MAIN_WIN_WIDTH, MAIN_WIN_HEIGHT, HUD_WIDTH, HUD_HEIGHT
import wind


class Panel(object):
    def __init__(self, game, offset, size):
        self.game = game
        self.width, self.height = size
        self.offset = offset
        self.hud_surface = pygame.Surface(size, pygame.SRCALPHA).convert_alpha()
        self.hud = Renderer(self.hud_surface)
        self.objects = []
        self.button_font = pygame.font.Font(None, 40)
        self.get_wind_button = Button(self.hud_surface, self.button_font, "Wind:", (self.width / 2 - 80, 10),
                                      on_click=self.get_wind)
        self.shoot_button = Button(self.hud_surface, self.button_font, "Shoot", (self.width / 2 - 80, 60),
                                   on_click=self.shoot)
        self.end_move_button = Button(self.hud_surface, self.button_font, "End move", (self.width / 2 - 80, 90),
                                      on_click=self.end_move)
        self.objects.append(self.get_wind_button)
        self.objects.append(self.shoot_button)
        self.objects.append(self.end_move_button)

    def get_wind(self):
        self.get_wind_button.disable()
        self.game.wind_type = random.sample(wind.WIND_TYPES, 1)[0]
        if self.game.wind_type != wind.STILLE:
            self.game.wind_direction = random.sample(wind.WIND_DIRECTIONS, 1)[0]
            self.get_wind_button.text = "Wind: {}, {}".format(wind.wind_type_to_str(self.game.wind_type),
                                                              wind.wind_direction_to_str(self.game.wind_direction))
        else:
            self.get_wind_button.text = "Wind: {}".format(wind.wind_type_to_str(self.game.wind_type))
        if self.game.wind_type == wind.STORM:
            self.game.force_ships_move()

    def shoot(self):
        miss = random.randint(0, 2)
        if self.game.player == PLAYER1:
            ships_to_shoot = self.game.yellow_ships
        else:
            ships_to_shoot = self.game.green_ships
        for ship in ships_to_shoot:
            ship.shoot(not miss)
        self.game.allsprites = self.game.layers_handler.get_all_sprites()
        self.game.yellow_ships = filter(lambda s: s.is_alive(), self.game.yellow_ships)
        self.game.green_ships = filter(lambda s: s.is_alive(), self.game.green_ships)
        self.game.ships = self.game.yellow_ships + self.game.green_ships

    def end_move(self):
        if self.game.player == PLAYER1:
            self.game.player = PLAYER2
        else:
            self.game.player = PLAYER1
        self.get_wind_button.enable()
        self.get_wind_button.text = "Wind:"
        self.game.wind_type = None
        for ship in self.game.ships:
            ship.reset()

    def draw(self):
        self.hud.fill([21, 37, 45]) # fill with water color
        self.hud.draw()
        pygame.draw.line(self.hud_surface, (44, 92, 118), [0, 0], [self.width, 0], 2)
        for obj in self.objects:
            obj.draw()
        self.game.screen.blit(self.hud_surface, self.offset)

    def mouseover(self, event_position):
        for obj in self.objects:
            obj.mouseover(map(lambda x, y: x - y, event_position, self.offset))

    def check_click(self, event_position):
        for obj in self.objects:
            obj.check_click(map(lambda x, y: x - y, event_position, self.offset))


class Game(object):
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(DISPLAY)
        pygame.display.set_caption("Nautili")
        self.bg_surface = pygame.Surface((MAIN_WIN_WIDTH, MAIN_WIN_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self.panel = Panel(self, (0, MAIN_WIN_HEIGHT), (HUD_WIDTH, HUD_HEIGHT))
        #fg = pygame.Surface((MAIN_WIN_WIDTH, MAIN_WIN_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self.layers_handler = lh = LayersHandler(tmxloader.load_pygame("./maps/map1.tmx", pixelalpha=True))
        self.background = IsometricRenderer(self.layers_handler, self.bg_surface)
        #foreground = Renderer(layers_handler, fg)
        self.allsprites = lh.get_all_sprites()
        self.clickable_objects_list = lh.get_clickable_objects()
        self.sea = lh.sea
        self.highlighted_sea = lh.highlighted_sea
        self.fire = lh.fire
        self.rocks = lh.rocks
        self.islands = lh.islands
        self.ships = lh.ships
        self.yellow_ships = lh.yellow_ships
        self.green_ships = lh.green_ships
        self.ports = lh.ports
        #background.fill([51, 88, 20]) # fill with grass color
        self.background.fill([21, 37, 45]) # fill with water color
        self.background.add(self.sea + self.rocks + self.islands)
        self.wind_type = None
        self.wind_direction = None
        self.player = PLAYER1

    def game_ended(self):
        if not self.yellow_ships:
            print "Green won!"
            return True
        elif not self.green_ships:
            print "Yellow won!"
            return True
        return False

    def max_storm_move(self):
        return sorted(self.ships, key=lambda ship: ship.storm_move, reverse=True)[0].storm_move

    def force_ships_move(self):
        # TODO: range to max ship storm move
        if self.player == PLAYER1:
            ships_to_move = self.yellow_ships
        else:
            ships_to_move = self.green_ships
        for x in xrange(0, self.max_storm_move()):
            for ship in ships_to_move:
                ship.calculate_moves(self.game.wind_type, self.game.wind_direction,
                                     obstacles=self.layers_handler.move_obstacles +
                                               map(lambda x: x.coords(), self.ships) +
                                               map(lambda y: y.coords(), self.ports),
                                     max=1)
                ship.move()

    def start(self):
        #foreground.add(islands)
        background = self.background
        panel = self.panel
        background.draw()
        #foreground.draw()
        selected_ship = None
        target_ship = None
        highlighted = None
        while not self.game_ended():
            for e in pygame.event.get():
                clicked = False
                if e.type == pygame.QUIT:
                    raise SystemExit, "QUIT"
                if e.type == pygame.MOUSEBUTTONDOWN and (e.button == 1 or e.button == 3):
                    for object in self.clickable_objects_list:
                        clicked = object.check_click(e.pos)
                        if clicked: break
                    else:
                        if not panel.check_click(e.pos) and selected_ship:
                            #selected_ship.aim_reset()
                            selected_ship = None
                            background.update(self.sea + self.rocks + self.islands)
                    if clicked:
                        # Check whether there's an object
                        if e.button == 1:
                            try:
                                if self.player == PLAYER1:
                                    ships_to_select = self.yellow_ships
                                else:
                                    ships_to_select = self.green_ships
                                selected_ship = filter(lambda obj: obj.coords() == (clicked.coords()), ships_to_select)[0]
                                #print "Object {} clicked".format(selected_ship)
                                # Highlight possible movements
                                highlighted = selected_ship.calculate_moves(self.wind_type, self.wind_direction,
                                                                            obstacles=self.layers_handler.move_obstacles + map(
                                                                                lambda x: x.coords(), self.ships) + map(
                                                                                lambda x: x.coords(), self.ports))
                                shots = selected_ship.calculate_shots(obstacles=self.layers_handler.shoot_obstacles)
                                background.update(self.sea + self.rocks + self.islands +
                                                  LayersHandler.filter_layer(self.highlighted_sea, highlighted) +
                                                  LayersHandler.filter_layer(self.fire, shots))
                            except IndexError:
                                if selected_ship:
                                    # we clicked on empty sea - move object there
                                    selected_ship.move(clicked.coords())
                                    self.allsprites = self.layers_handler.get_all_sprites()
                                    background.update(self.sea + self.rocks + self.islands)
                                    selected_ship = None
                        else:
                            try:
                                target_ship = filter(lambda obj: obj.coords() == (clicked.coords()), self.ships)[0]
                                if selected_ship and selected_ship != target_ship:
                                    if selected_ship.aim(target_ship):
                                        # Draw curved arrow to the target
                                        background.clear()
                                        background.add(self.sea + self.rocks + self.islands +
                                                       LayersHandler.filter_layer(self.highlighted_sea, highlighted) +
                                                       LayersHandler.filter_layer(self.fire, shots))
                                        (x0, y0) = self.layers_handler.isometric_to_orthogonal(selected_ship.x, selected_ship.y)
                                        for target in selected_ship.get_targets():
                                            (x1, y1) = self.layers_handler.isometric_to_orthogonal(target.x, target.y)
                                            background.add_line((x0, y0), (x1, y1))
                                        background.draw()
                            except IndexError:
                                pass
            # Process HUD mouseover
            panel.mouseover(pygame.mouse.get_pos())
            # end event handing
            self.screen.blit(self.bg_surface, (0, 0))
            self.panel.draw()
            self.allsprites.update()
            self.allsprites.draw(self.screen)
            #screen.blit(fg, (0, 0))
            pygame.display.update()