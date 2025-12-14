"""Este código es un simulador de un lanzamiento paravolico.
El usuario, utilizando las flechas del teclado, puede ajustar el angulo de lanzamiento, la flecha hacia arriba aumenta el angulo y la flecha hacia abajo lo disminuye;
luego, al presionar la barra espaciadora, se lanza el proyectil y se observa su trayectoria sin contar los factores del entorno, para aumentar la dificultad.
La fuerza con la que se lanza el proyectil se ajusta utilizando la w (para aumentar la fuerza) y la s (para disminuir la fuerza).
El objetivo es aterrizar el proyectil lo más cerca posible de un objetivo fijo.
La gravedad, viento, rozamiento con el aire variaran en cada ronda para aumentar la dificultad.
Son 3 rondas en total.
En cada ronda, el usuario tiene 5 intentos para acertar el objetivo.
La diana cambia de posición cada vez que se cambia de ronda.
El juego termina cuando se completan las 3 rondas o el usuario falla los 5 intentos en cualquier ronda.
Al pasar de ronda, suena una melodia de victoria, si el usuario pierde, suena una melodia de derrota.
"""
import math
import random
import sys
import pygame
from typing import List, Tuple, Optional

# --- CONFIGURACIÓN ---
class Config:
    WIDTH = 900
    HEIGHT = 600
    FPS = 60
    GRAVITY = 9.81 * 100
    TITLE = "Cañón Pro"

class Colors:
    SKY_TOP = (100, 149, 237)
    SKY_BOTTOM = (224, 255, 255)
    GROUND = (34, 139, 34)
    TEXT = (255, 255, 255)
    CANNON = (60, 60, 60)
    PROJECTILE = (220, 20, 60)
    PROJECTILE_TRAIL = (200, 200, 200)
    TARGET = (255, 69, 0)
    BUTTON = (70, 130, 180)
    BUTTON_HOVER = (100, 160, 210)

class PhysicsParams:
    PROJECTILE_RADIUS = 6
    TARGET_RADIUS = 20
    CANNON_LENGTH = 50
    CANNON_POS = (60, Config.HEIGHT - 70)

# --- UTILIDADES ---
def clamp(v, a, b):
    return max(a, min(b, v))

def draw_gradient(surface, top, bottom):
    for y in range(surface.get_height()):
        r = top[0] + (bottom[0]-top[0]) * y / surface.get_height()
        g = top[1] + (bottom[1]-top[1]) * y / surface.get_height()
        b = top[2] + (bottom[2]-top[2]) * y / surface.get_height()
        pygame.draw.line(surface, (int(r),int(g),int(b)), (0,y), (Config.WIDTH,y))

# --- PROYECTIL ---
class Projectile:
    def __init__(self, x, y, vx, vy):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.alive = True
        self.trail: List[Tuple[int,int]] = []

    def update(self, dt):
        self.vy += Config.GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 150:
            self.trail.pop(0)
        if self.y > Config.HEIGHT or self.x < 0 or self.x > Config.WIDTH:
            self.alive = False

    def draw(self, screen):
        if len(self.trail) > 1:
            pygame.draw.lines(screen, Colors.PROJECTILE_TRAIL, False, self.trail, 2)
        pygame.draw.circle(screen, Colors.PROJECTILE, (int(self.x), int(self.y)), PhysicsParams.PROJECTILE_RADIUS)

# --- DIANA MÓVIL ---
class Target:
    def __init__(self):
        self.base_x = random.randint(400, Config.WIDTH - 80)
        self.y = random.randint(200, Config.HEIGHT - 120)
        self.radius = PhysicsParams.TARGET_RADIUS
        self.time = 0
        self.amplitude = random.randint(80, 200)
        self.speed = random.uniform(1.0, 2.0)
        self.x = self.base_x

    def update(self, dt):
        self.time += dt
        self.x = self.base_x + math.sin(self.time * self.speed) * self.amplitude

    def draw(self, screen):
        pygame.draw.circle(screen, Colors.TARGET, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255,255,255), (int(self.x), int(self.y)), int(self.radius*0.6))

    def hit(self, p):
        dx = self.x - p.x
        dy = self.y - p.y
        return dx*dx + dy*dy <= (self.radius + PhysicsParams.PROJECTILE_RADIUS)**2

# --- GAME ---
class GameManager:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption(Config.TITLE)
        self.clock = pygame.time.Clock()

        self.font_ui = pygame.font.SysFont("Verdana", 14)
        self.font_big = pygame.font.SysFont("Verdana", 48, bold=True)

        self.sound_win = pygame.mixer.Sound("victory.wav")
        self.sound_lose = pygame.mixer.Sound("defeat.wav")

        self.round3_image = pygame.image.load("round3.png").convert_alpha()
        self.show_round3 = False
        self.round3_timer = 0

        self.reset_game()

    def reset_game(self):
        self.angle = 45
        self.power = 500
        self.projectile: Optional[Projectile] = None
        self.round = 1
        self.max_rounds = 3
        self.attempts = 5
        self.target = Target()
        self.game_over = False
        self.win = False
        self.show_round3 = False
        pygame.mixer.stop()

    def fire(self):
        rad = math.radians(self.angle)
        cx, cy = PhysicsParams.CANNON_POS
        x = cx + PhysicsParams.CANNON_LENGTH * math.cos(rad)
        y = cy - PhysicsParams.CANNON_LENGTH * math.sin(rad)
        vx = math.cos(rad) * self.power
        vy = -math.sin(rad) * self.power
        self.projectile = Projectile(x, y, vx, vy)

    def update(self, dt):
        if self.game_over:
            return

        if self.show_round3:
            self.round3_timer -= dt
            if self.round3_timer <= 0:
                self.show_round3 = False
            return

        self.target.update(dt)

        if self.projectile:
            self.projectile.update(dt)
            if self.target.hit(self.projectile):
                self.round += 1
                self.projectile = None
                if self.round == 3:
                    self.show_round3 = True
                    self.round3_timer = 3
                if self.round > self.max_rounds:
                    self.win = True
                    self.game_over = True
                    self.sound_win.play(-1)
                else:
                    self.attempts = 5
                    self.target = Target()
            elif not self.projectile.alive:
                self.projectile = None
                self.attempts -= 1
                if self.attempts <= 0:
                    self.game_over = True
                    self.sound_lose.play(-1)

    def draw_prediction(self):
        rad = math.radians(self.angle)
        cx, cy = PhysicsParams.CANNON_POS
        sim_x = cx + PhysicsParams.CANNON_LENGTH * math.cos(rad)
        sim_y = cy - PhysicsParams.CANNON_LENGTH * math.sin(rad)
        sim_vx = math.cos(rad) * self.power
        sim_vy = -math.sin(rad) * self.power
        dt_sim = 1/Config.FPS
        points = []
        for _ in range(300):
            sim_vy += Config.GRAVITY * dt_sim
            sim_x += sim_vx * dt_sim
            sim_y += sim_vy * dt_sim
            if sim_y > Config.HEIGHT or sim_x < 0 or sim_x > Config.WIDTH:
                break
            points.append((int(sim_x), int(sim_y)))
        for i in range(0, len(points)-1, 2):
            pygame.draw.line(self.screen, (50,50,50), points[i], points[i+1], 2)

    def draw_button(self, text, rect):
        mouse = pygame.mouse.get_pos()
        color = Colors.BUTTON_HOVER if rect.collidepoint(mouse) else Colors.BUTTON
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        label = self.font_ui.render(text, True, (255,255,255))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def draw(self):
        draw_gradient(self.screen, Colors.SKY_TOP, Colors.SKY_BOTTOM)
        pygame.draw.rect(self.screen, Colors.GROUND, (0, Config.HEIGHT-60, Config.WIDTH, 60))

        cx, cy = PhysicsParams.CANNON_POS
        rad = math.radians(self.angle)
        ex = cx + PhysicsParams.CANNON_LENGTH * math.cos(rad)
        ey = cy - PhysicsParams.CANNON_LENGTH * math.sin(rad)
        pygame.draw.circle(self.screen, (40,40,40), (cx, cy), 20)
        pygame.draw.line(self.screen, Colors.CANNON, (cx, cy), (ex, ey), 10)

        if self.show_round3:
            rect = self.round3_image.get_rect(center=(Config.WIDTH//2, Config.HEIGHT//2))
            self.screen.blit(self.round3_image, rect)
        else:
            self.draw_prediction()
            self.target.draw(self.screen)
            if self.projectile:
                self.projectile.draw(self.screen)
            ui = self.font_ui.render(f"Ronda {self.round}/3 | Intentos {self.attempts}", True, Colors.TEXT)
            self.screen.blit(ui, (10,10))

        if self.game_over and not self.show_round3:
            msg = "¡HAS GANADO!" if self.win else "HAS PERDIDO"
            txt = self.font_big.render(msg, True, (255,215,0))
            self.screen.blit(txt, txt.get_rect(center=(Config.WIDTH//2, 200)))
            self.button_rect = pygame.Rect(Config.WIDTH//2 - 80, 300, 160, 50)
            self.draw_button("Volver a jugar", self.button_rect)

        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(Config.FPS) / 1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN and not self.game_over and not self.show_round3:
                    if e.key == pygame.K_SPACE and not self.projectile:
                        self.fire()
                if e.type == pygame.MOUSEBUTTONDOWN and self.game_over:
                    if self.button_rect.collidepoint(e.pos):
                        self.reset_game()

            keys = pygame.key.get_pressed()
            if not self.game_over and not self.show_round3:
                if keys[pygame.K_UP]:
                    self.angle = clamp(self.angle + 60*dt, 10, 85)
                if keys[pygame.K_DOWN]:
                    self.angle = clamp(self.angle - 60*dt, 10, 85)
                if keys[pygame.K_RIGHT]:
                    self.power = clamp(self.power + 300*dt, 100, 1500)
                if keys[pygame.K_LEFT]:
                    self.power = clamp(self.power - 300*dt, 100, 1500)

            self.update(dt)
            self.draw()

if __name__ == "__main__":
    GameManager().run()
