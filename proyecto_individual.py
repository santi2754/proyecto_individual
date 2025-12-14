import math
import random
import sys
import os
import json
import pygame
from typing import List, Tuple, Optional, Dict

# --- CONFIGURACIÓN Y CONSTANTES ---

class Config:
    """Configuración general del juego"""
    WIDTH: int = 900
    HEIGHT: int = 600
    FPS: int = 60
    GRAVITY: float = 9.81 * 100
    TITLE: str = "Cañón Pro: Edición Deluxe"
    SCORE_FILE: str = "highscore.json"

class Colors:
    """Paleta de colores mejorada"""
    SKY_TOP = (100, 149, 237)      # Cornflower Blue
    SKY_BOTTOM = (224, 255, 255)   # Light Cyan
    GROUND = (34, 139, 34)         # Forest Green
    GROUND_TOP = (50, 205, 50)     # Lime Green (borde)
    TEXT = (255, 255, 255)
    UI_BG = (0, 0, 0, 150)         # Fondo semitransparente para UI
    CANNON = (60, 60, 60)
    PROJECTILE = (220, 20, 60)     # Crimson
    PROJECTILE_TRAIL = (200, 200, 200)
    TARGET_OUTER = (255, 69, 0)    # Red Orange
    TARGET_INNER = (255, 255, 255)
    PREDICTION_LINE = (50, 50, 50)
    PARTICLE = [(255, 215, 0), (255, 69, 0), (255, 255, 255)] # Gold, Orange, White

class PhysicsParams:
    """Parámetros físicos por defecto"""
    PROJECTILE_RADIUS = 6
    BASE_TARGET_RADIUS = 20
    DRAG_COEFF = 0.02
    CANNON_LENGTH = 50
    CANNON_POS = (60, Config.HEIGHT - 70)

# --- UTILIDADES ---

def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))

def draw_gradient(surface, top_color, bottom_color):
    """Dibuja un degradado vertical de fondo."""
    height = surface.get_height()
    # Para optimizar, dibujamos líneas o rectángulos pequeños interpolando color
    # Nota: En un juego muy complejo esto se pre-renderizaría.
    for y in range(height):
        ratio = y / height
        r = top_color[0] * (1 - ratio) + bottom_color[0] * ratio
        g = top_color[1] * (1 - ratio) + bottom_color[1] * ratio
        b = top_color[2] * (1 - ratio) + bottom_color[2] * ratio
        pygame.draw.line(surface, (int(r), int(g), int(b)), (0, y), (Config.WIDTH, y))

# --- SISTEMA DE PUNTUACIÓN ---

class ScoreManager:
    """Gestiona la persistencia de la puntuación."""
    def __init__(self):
        self.current_streak = 0
        self.best_streak = 0
        self.total_hits = 0
        self.load_data()

    def add_hit(self):
        self.current_streak += 1
        self.total_hits += 1
        if self.current_streak > self.best_streak:
            self.best_streak = self.current_streak
            self.save_data()

    def reset_streak(self):
        self.current_streak = 0

    def load_data(self):
        if os.path.exists(Config.SCORE_FILE):
            try:
                with open(Config.SCORE_FILE, 'r') as f:
                    data = json.load(f)
                    self.best_streak = data.get('best_streak', 0)
            except Exception as e:
                print(f"Error cargando puntuación: {e}")

    def save_data(self):
        try:
            with open(Config.SCORE_FILE, 'w') as f:
                json.dump({'best_streak': self.best_streak}, f)
        except Exception as e:
            print(f"Error guardando puntuación: {e}")

# --- EFECTOS VISUALES ---

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-150, 150)
        self.vy = random.uniform(-150, 150)
        self.life = random.uniform(0.5, 1.0) # Segundos de vida
        self.color = random.choice(Colors.PARTICLE)
        self.size = random.randint(2, 5)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        self.size = max(0, self.size - 2 * dt) # Se hace pequeña

    def draw(self, surface):
        if self.life > 0:
            s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, self.color + (int(255 * self.life),), (self.size, self.size), self.size)
            surface.blit(s, (self.x - self.size, self.y - self.size))

# --- CLASES DEL JUEGO ---

class Projectile:
    def __init__(self, x: float, y: float, vx: float, vy: float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = PhysicsParams.PROJECTILE_RADIUS
        self.alive = True
        self.trail: List[Tuple[int, int]] = []

    def update(self, dt: float, wind_accel: float, drag_enabled: bool) -> None:
        ax = wind_accel
        ay = Config.GRAVITY

        if drag_enabled:
            ax -= PhysicsParams.DRAG_COEFF * self.vx
            ay -= PhysicsParams.DRAG_COEFF * self.vy

        self.vx += ax * dt
        self.vy += ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 150: # Limitamos estela para rendimiento visual
            self.trail.pop(0)

        # Colisión con bordes
        if (self.y - self.radius > Config.HEIGHT or 
            self.x - self.radius > Config.WIDTH or 
            self.x + self.radius < 0):
            self.alive = False

    def draw(self, surface: pygame.Surface, show_trail: bool) -> None:
        if show_trail and len(self.trail) > 1:
            pygame.draw.lines(surface, Colors.PROJECTILE_TRAIL, False, self.trail, 2)
        
        pygame.draw.circle(surface, (0,0,0), (int(self.x), int(self.y)), self.radius + 1) # Borde
        pygame.draw.circle(surface, Colors.PROJECTILE, (int(self.x), int(self.y)), self.radius)

class Target:
    def __init__(self, x: float, y: float, mobile: bool = False):
        self.base_x = x
        self.x = x
        self.y = y
        self.radius = PhysicsParams.BASE_TARGET_RADIUS
        self.mobile = mobile
        self.time_elapsed = 0.0
        self.amplitude = random.uniform(80, 200)
        self.base_speed = random.uniform(0.8, 1.8)
        self.speed_multiplier = 1.0

    def change_size(self, delta: int):
        self.radius = clamp(self.radius + delta, 10, 60)

    def change_speed(self, delta: float):
        self.speed_multiplier = clamp(self.speed_multiplier + delta, 0.1, 5.0)

    def update(self, dt: float) -> None:
        if self.mobile:
            self.time_elapsed += dt
            current_speed = self.base_speed * self.speed_multiplier
            self.x = self.base_x + math.sin(self.time_elapsed * current_speed) * self.amplitude

    def draw(self, surface: pygame.Surface) -> None:
        pos = (int(self.x), int(self.y))
        # Estilo "Diana" (Anillos)
        pygame.draw.circle(surface, (255, 255, 255), pos, self.radius + 2) # Borde blanco externo
        pygame.draw.circle(surface, Colors.TARGET_OUTER, pos, self.radius)
        pygame.draw.circle(surface, (255, 255, 255), pos, int(self.radius * 0.7))
        pygame.draw.circle(surface, Colors.TARGET_OUTER, pos, int(self.radius * 0.4))

    def check_collision(self, proj: Projectile) -> bool:
        dx = self.x - proj.x
        dy = self.y - proj.y
        dist_sq = dx*dx + dy*dy
        return dist_sq <= (self.radius + proj.radius)**2

class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption(Config.TITLE)
        self.clock = pygame.time.Clock()
        self.score_manager = ScoreManager()
        
        # Fuentes
        self.font_ui = pygame.font.SysFont("Verdana", 14)
        self.font_msg = pygame.font.SysFont("Verdana", 50, bold=True)

        # Estado
        self.running = True
        self.angle = 45.0
        self.power = 500.0
        self.message = ""
        self.message_timer = 0.0
        self.particles: List[Particle] = []
        
        # Opciones
        self.enable_wind = False
        self.enable_drag = False
        self.show_trail = True
        self.mobile_target_enabled = True
        self.wind_accel = 0.0

        self.projectile: Optional[Projectile] = None
        self.target = self._create_target()

    def _create_target(self) -> Target:
        x_pos = random.randint(400, Config.WIDTH - 100)
        # Mantener configuraciones previas si existen
        old_radius = self.target.radius if hasattr(self, 'target') else PhysicsParams.BASE_TARGET_RADIUS
        old_speed_mult = self.target.speed_multiplier if hasattr(self, 'target') else 1.0
        
        t = Target(x_pos, Config.HEIGHT - 120, mobile=self.mobile_target_enabled)
        t.radius = old_radius
        t.speed_multiplier = old_speed_mult
        return t

    def handle_input(self, dt: float) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event)

        keys = pygame.key.get_pressed()
        MIN_ANGLE = 40.0 
        
        if keys[pygame.K_RIGHT]: self.power = clamp(self.power + 300 * dt, 50, 1500)
        if keys[pygame.K_LEFT]: self.power = clamp(self.power - 300 * dt, 50, 1500)
        if keys[pygame.K_UP]: 
            self.angle = clamp(self.angle + 60 * dt, MIN_ANGLE, 90)
        if keys[pygame.K_DOWN]: 
            self.angle = clamp(self.angle - 60 * dt, MIN_ANGLE, 90)

    def _handle_keydown(self, event):
        if event.key == pygame.K_SPACE and self.projectile is None:
            self._fire_projectile()
        elif event.key == pygame.K_r:
            self._reset_round(hit=False) # Reset manual rompe la racha? Opcional. Aquí no.
        
        # Modificadores de Objetivo
        elif event.key == pygame.K_m:
            self.mobile_target_enabled = not self.mobile_target_enabled
            self.target.mobile = self.mobile_target_enabled
        elif event.key == pygame.K_q: # q Disminuir tamaño
            self.target.change_size(-5)
        elif event.key == pygame.K_e: # e Aumentar tamaño
            self.target.change_size(5)
        elif event.key == pygame.K_MINUS or event.unicode == '-': 
            self.target.change_speed(-0.2)
        elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS or event.unicode == '+': 
            self.target.change_speed(0.2)

        # Modificadores de entorno
        elif event.key == pygame.K_w:
            self.enable_wind = not self.enable_wind
            self.wind_accel = random.uniform(-300, 300) if self.enable_wind else 0.0
        elif event.key == pygame.K_d:
            self.enable_drag = not self.enable_drag
        elif event.key == pygame.K_t:
            self.show_trail = not self.show_trail
        elif event.key == pygame.K_ESCAPE:
            self.running = False

    def _fire_projectile(self):
        rad = math.radians(self.angle)
        cx, cy = PhysicsParams.CANNON_POS
        start_x = cx + PhysicsParams.CANNON_LENGTH * math.cos(rad)
        start_y = cy - PhysicsParams.CANNON_LENGTH * math.sin(rad)
        vx = math.cos(rad) * self.power
        vy = -math.sin(rad) * self.power
        self.projectile = Projectile(start_x, start_y, vx, vy)

    def _spawn_particles(self, x, y):
        for _ in range(30):
            self.particles.append(Particle(x, y))

    def _reset_round(self, hit: bool):
        self.projectile = None
        if hit:
            self.target = self._create_target()
        self.message = ""

    def update(self, dt: float) -> None:
        self.target.update(dt)
        
        # Actualizar partículas
        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)

        if self.projectile:
            wind = self.wind_accel if self.enable_wind else 0.0
            self.projectile.update(dt, wind, self.enable_drag)
            
            # Chequeo colisión
            if self.target.check_collision(self.projectile):
                self.score_manager.add_hit()
                self._spawn_particles(self.target.x, self.target.y)
                self.message = "¡DIANA!"
                self.message_timer = 2.0
                self.projectile.alive = False
                self._reset_round(hit=True)
            
            # Chequeo fallo (suelo o limites)
            elif not self.projectile.alive:
                self.score_manager.reset_streak()
                self.message = "Fallo..."
                self.message_timer = 1.0
                self.projectile = None

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

    def _draw_prediction(self):
        rad = math.radians(self.angle)
        cx, cy = PhysicsParams.CANNON_POS
        sim_x = cx + PhysicsParams.CANNON_LENGTH * math.cos(rad)
        sim_y = cy - PhysicsParams.CANNON_LENGTH * math.sin(rad)
        sim_vx = math.cos(rad) * self.power
        sim_vy = -math.sin(rad) * self.power
        
        sim_dt = 0.05
        wind = self.wind_accel if self.enable_wind else 0.0
        
        points = []
        for _ in range(40): # Menos puntos para que sea solo una guía corta
            ax = wind
            ay = Config.GRAVITY
            if self.enable_drag:
                ax -= PhysicsParams.DRAG_COEFF * sim_vx
                ay -= PhysicsParams.DRAG_COEFF * sim_vy
            
            sim_vx += ax * sim_dt
            sim_vy += ay * sim_dt
            sim_x += sim_vx * sim_dt
            sim_y += sim_vy * sim_dt
            
            if sim_y > Config.HEIGHT - 60: break
            points.append((int(sim_x), int(sim_y)))

        if len(points) > 1:
            for i in range(0, len(points) - 1, 2):
                if i+1 < len(points):
                    pygame.draw.line(self.screen, Colors.PREDICTION_LINE, points[i], points[i+1], 2)

    def draw(self) -> None:
        draw_gradient(self.screen, Colors.SKY_TOP, Colors.SKY_BOTTOM)
        
        # Suelo
        pygame.draw.rect(self.screen, Colors.GROUND, (0, Config.HEIGHT - 60, Config.WIDTH, 60))
        pygame.draw.rect(self.screen, Colors.GROUND_TOP, (0, Config.HEIGHT - 65, Config.WIDTH, 5))

        # Cañón
        rad = math.radians(self.angle)
        cx, cy = PhysicsParams.CANNON_POS
        end_x = cx + PhysicsParams.CANNON_LENGTH * math.cos(rad)
        end_y = cy - PhysicsParams.CANNON_LENGTH * math.sin(rad)
        
        # Base rueda
        pygame.draw.circle(self.screen, (40, 40, 40), (cx, cy), 20)
        # Tubo
        pygame.draw.line(self.screen, Colors.CANNON, (cx, cy), (end_x, end_y), 12)
        
        # Elementos juego
        self._draw_prediction()
        self.target.draw(self.screen)
        
        for p in self.particles:
            p.draw(self.screen)

        if self.projectile:
            self.projectile.draw(self.screen, self.show_trail)

        self._draw_ui()
        pygame.display.flip()

    def _draw_ui(self):
        # Panel de fondo para UI
        ui_bg = pygame.Surface((320, 190), pygame.SRCALPHA)
        ui_bg.fill(Colors.UI_BG)
        self.screen.blit(ui_bg, (5, 5))

        infos = [
            f"RACHA ACTUAL: {self.score_manager.current_streak}",
            f"MEJOR RACHA: {self.score_manager.best_streak}",
            "---------------------------",
            f"Ángulo: {self.angle:.1f}° | Potencia: {self.power:.0f}",
            f"Viento: {self.wind_accel:.0f} | Drag: {'SI' if self.enable_drag else 'NO'}",
            f"Diana Vel: x{self.target.speed_multiplier:.1f} | Radio: {self.target.radius}",
            "---------------------------",
            "q / e : Tamaño Diana",
            "- / + : Velocidad Diana",
            "M: Movimiento | W: Viento"
        ]

        for i, line in enumerate(infos):
            color = (255, 215, 0) if "RACHA" in line else Colors.TEXT
            surf = self.font_ui.render(line, True, color)
            self.screen.blit(surf, (15, 15 + i * 18))

        if self.message:
            # Sombra del texto
            shadow = self.font_msg.render(self.message, True, (0,0,0))
            msg = self.font_msg.render(self.message, True, (255, 255, 0))
            center_x = Config.WIDTH // 2
            self.screen.blit(shadow, shadow.get_rect(center=(center_x + 2, 102)))
            self.screen.blit(msg, msg.get_rect(center=(center_x, 100)))

    def run(self):
        while self.running:
            dt = self.clock.tick(Config.FPS) / 1000.0
            self.handle_input(dt)
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    GameManager().run()