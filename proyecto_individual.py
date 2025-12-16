""" Este código implementa un juego de tiro parabólico utilizando Pygame. El jugador controla un cañón para disparar proyectiles
hacia una diana móvil, con el objetivo de acertar en la diana en varias rondas. El juego incluye física básica, detección de colisiones,
una interfaz de usuario simple y efectos visuales como una estela para el proyectil y un degradado de fondo. 
El juego termina cuando el jugador gana al acertar en todas las rondas o pierde al quedarse sin intentos. 
El código está estructurado en varias clases para manejar la configuración, colores, física, proyectiles, dianas y el funcionamiento general del juego.

Ejemplo de uso:
    Para ejecutar el juego, asegúrate de tener Pygame instalado y los archivos de sonido e imagen necesarios en el mismo directorio que este script.
    Luego, simplemente ejecuta este script en tu entorno de Python.
    1. El usuario puede controlar el ángulo y la potencia del disparo utilizando las teclas de flecha.
    2. Presiona la barra espaciadora para disparar el proyectil.
    3. El objetivo es acertar en la diana móvil en tres rondas, con un número limitado de intentos.
    4. El juego muestra una pantalla de victoria o derrota al final, con la opción de reiniciar el juego.
"""
import math
import random
import sys
import pygame
from typing import List, Tuple, Optional

class configuracion:
    ancho = 900
    alto = 600
    fps = 60
    gravedad = 9.81 * 100
    titulo = "Tiro parabólico"

class colores:
    # fondo
    cielo_superior = (100, 149, 237)
    cielo_inferior = (224, 255, 255)
    suelo = (34, 139, 34)
    # elementos del juego
    texto = (255, 255, 255)
    canon = (60, 60, 60)         # canon=cañón
    proyectil = (220, 20, 60)
    estela_proyectil = (200, 200, 200)
    diana = (255, 69, 0)
    # botones
    boton = (70, 130, 180)
    boton_hover = (100, 160, 210)

class fisica:
    # tamaños de los objetos
    radio_proyectil = 6
    radio_diana = 20
    longitud_canon = 50
    posicion_canon = (60, configuracion.alto - 70)

def limitar(valor, minimo, maximo):     # limitar un valor entre un mínimo y un máximo
    return max(minimo, min(maximo, valor))

def dibujar_degradado(superficie, superior, inferior):   # dibujar un degradado en el fondo, para que quede mejor visualmente
    for y in range(superficie.get_height()):
        r = superior[0] + (inferior[0] - superior[0]) * y / superficie.get_height()
        g = superior[1] + (inferior[1] - superior[1]) * y / superficie.get_height()
        b = superior[2] + (inferior[2] - superior[2]) * y / superficie.get_height()
        pygame.draw.line(superficie, (int(r), int(g), int(b)), (0, y), (configuracion.ancho, y))

class proyectil:
    def __init__(self, x, y, velocidad_x, velocidad_y):
        self.x = x     # posición del proyectil
        self.y = y
        self.velocidad_x = velocidad_x    # velocidad
        self.velocidad_y = velocidad_y
        self.activo = True     # estado del proyectil (si sigue en pantalla)
        self.estela: List[Tuple[int, int]] = []   # lista de posiciones para la estela

    def actualizar(self, delta_tiempo):
        self.velocidad_y += configuracion.gravedad * delta_tiempo  # actualización de la velocidad
        self.x += self.velocidad_x * delta_tiempo    # actualización de la posición
        self.y += self.velocidad_y * delta_tiempo
        self.estela.append((int(self.x), int(self.y)))   # guarda la posición para crear la estela
        if len(self.estela) > 150:
            self.estela.pop(0)
        elif (self.y > configuracion.alto or self.x < 0 or self.x > configuracion.ancho):  # fuera de pantalla
            self.activo = False

    def dibujar(self, pantalla):      # estela antes de dibujar el proyectil
        if len(self.estela) > 1:
            pygame.draw.lines(pantalla, colores.estela_proyectil, False, self.estela, 2)
            pygame.draw.circle(pantalla, colores.proyectil, (int(self.x), int(self.y)), fisica.radio_proyectil)

class diana:
    def __init__(self):
        self.base_x = random.randint(400, configuracion.ancho - 80)   # posicion aleatoria de la diana
        self.y = random.randint(200, configuracion.alto - 120)
        self.radio = fisica.radio_diana     # tamaño de la diana
        self.tiempo = 0
        self.amplitud = random.randint(80, 200)       # amplitud del movimiento
        self.velocidad = random.uniform(1.0, 2.0)     # velocidad del movimiento
        self.x = self.base_x

    def actualizar(self, delta_tiempo):        # movimiento de la diana
        self.tiempo += delta_tiempo
        self.x = self.base_x + math.sin(self.tiempo * self.velocidad) * self.amplitud

    def dibujar(self, pantalla):      # dibujar la diana
        pygame.draw.circle(pantalla, colores.diana, (int(self.x), int(self.y)), self.radio)
        pygame.draw.circle(pantalla, (255, 255, 255), (int(self.x), int(self.y)), int(self.radio * 0.6))

    def impacta(self, bala):   # comprobar si el proyectil impacta con la diana
        dx = self.x - bala.x
        dy = self.y - bala.y
        return dx * dx + dy * dy <= (self.radio + fisica.radio_proyectil) ** 2

class funcionaminento_juego:
    def __init__(self):      # inicialización de pygame
        pygame.init()
        pygame.mixer.init()
        self.pantalla = pygame.display.set_mode((configuracion.ancho, configuracion.alto)) # pantalla del juego
        pygame.display.set_caption(configuracion.titulo)
        self.reloj = pygame.time.Clock()
        self.fuente_ui = pygame.font.SysFont("Verdana", 14)   # fuente de la interfaz(texto)
        self.fuente_grande = pygame.font.SysFont("Verdana", 48, bold=True)
        self.sonido_ganar = pygame.mixer.Sound("victory.wav")  # sonidos de victoria y derrota
        self.sonido_perder = pygame.mixer.Sound("defeat.wav")
        self.imagen_ronda3 = pygame.image.load("round3.png").convert_alpha()   # imagen especial para la ronda 3
        self.mostrar_ronda3 = False
        self.temporizador_ronda3 = 0
        self.reiniciar_juego()

    def reiniciar_juego(self):    # poner el valor inicial a las variables del juego
        self.angulo = 45
        self.potencia = 500
        self.bala: Optional[proyectil] = None
        self.ronda = 1
        self.max_rondas = 3
        self.intentos = 3
        self.objetivo = diana()
        self.fin_juego = False
        self.gano = False
        self.mostrar_ronda3 = False
        pygame.mixer.stop()

    def disparar(self):
        radianes = math.radians(self.angulo) # direccion del disparo
        cx, cy = fisica.posicion_canon
        x = cx + fisica.longitud_canon * math.cos(radianes)   # posición inicial del proyectil
        y = cy - fisica.longitud_canon * math.sin(radianes)
        velocidad_x = math.cos(radianes) * self.potencia       #velocidad inicial del proyectil
        velocidad_y = -math.sin(radianes) * self.potencia
        self.bala = proyectil(x, y, velocidad_x, velocidad_y)   # crear el proyectil

    def actualizar(self, delta_tiempo):
        # Si el juego terminó, no se actualiza nada
        if self.fin_juego:
            return
        
        if self.mostrar_ronda3:             # pantalla especial de la ronda 3
            self.temporizador_ronda3 -= delta_tiempo
            if self.temporizador_ronda3 <= 0:
                self.mostrar_ronda3 = False
            return
        
        # actualizar diana
        self.objetivo.actualizar(delta_tiempo)

        # actualizar proyectil cuando está en pantalla
        if self.bala:
            self.bala.actualizar(delta_tiempo)

            if self.objetivo.impacta(self.bala):
                self.ronda += 1   # Acierto
                self.bala = None

                if self.ronda == 3:        # pantalla especial de la ronda 3
                    self.mostrar_ronda3 = True
                    self.temporizador_ronda3 = 3

                elif self.ronda > self.max_rondas:     # victoria
                    self.gano = True
                    self.fin_juego = True
                    self.sonido_ganar.play(-1)
                else:                                 # nueva diana y más intentos
                    self.intentos = 5
                    self.objetivo = diana()

            elif not self.bala.activo:     # fallo y derrota
                self.bala = None
                self.intentos -= 1

                if self.intentos <= 0:
                    self.fin_juego = True
                    self.sonido_perder.play(-1)

    def dibujar_prediccion(self):        # trayectoria "pintada" linea discontinua
        radianes = math.radians(self.angulo)
        cx, cy = fisica.posicion_canon
        x_sim = cx + fisica.longitud_canon * math.cos(radianes)
        y_sim = cy - fisica.longitud_canon * math.sin(radianes)
        vx_sim = math.cos(radianes) * self.potencia
        vy_sim = -math.sin(radianes) * self.potencia
        delta_sim = 1 / configuracion.fps    #prediccion de la trayectoria
        puntos = []

        for _ in range(300):                # simular 300 pasos
            vy_sim += configuracion.gravedad * delta_sim
            x_sim += vx_sim * delta_sim
            y_sim += vy_sim * delta_sim
            if (y_sim > configuracion.alto or x_sim < 0 or x_sim > configuracion.ancho):
                break
            puntos.append((int(x_sim), int(y_sim)))

        for i in range(0, len(puntos) - 1, 2):
            pygame.draw.line(self.pantalla, (50, 50, 50), puntos[i], puntos[i + 1], 2)

    def dibujar_boton(self, texto, rectangulo):
        raton = pygame.mouse.get_pos()
        color = (
            colores.boton_hover
            if rectangulo.collidepoint(raton)
            else colores.boton
        )
        pygame.draw.rect(self.pantalla, color, rectangulo,border_radius=8)
        etiqueta = self.fuente_ui.render(texto, True, (255, 255, 255))
        self.pantalla.blit(etiqueta, etiqueta.get_rect(center=rectangulo.center))

    def dibujar(self):
        # fondo
        dibujar_degradado(self.pantalla, colores.cielo_superior,colores.cielo_inferior)
        # suelo
        pygame.draw.rect(self.pantalla, colores.suelo, (0, configuracion.alto - 60, configuracion.ancho, 60))
        # cañón
        cx, cy = fisica.posicion_canon
        radianes = math.radians(self.angulo)
        ex = cx + fisica.longitud_canon * math.cos(radianes)
        ey = cy - fisica.longitud_canon * math.sin(radianes)
        pygame.draw.circle(self.pantalla, (40, 40, 40), (cx, cy), 20)
        pygame.draw.line(self.pantalla, colores.canon, (cx, cy), (ex, ey), 10)
        # en la ronda 3 se muestra la imagen, sino se dibujan los elementos del juego
        if self.mostrar_ronda3:
            rect = self.imagen_ronda3.get_rect(
                center=(configuracion.ancho // 2, configuracion.alto // 2)
            )
            self.pantalla.blit(self.imagen_ronda3, rect)
        else:
            self.dibujar_prediccion()
            self.objetivo.dibujar(self.pantalla)

            if self.bala:
                self.bala.dibujar(self.pantalla)

            texto_ui = self.fuente_ui.render(
                f"Ronda {self.ronda}/3 | Intentos {self.intentos}",
                True,
                colores.texto
            )
            self.pantalla.blit(texto_ui, (10, 10))

        # pantalla final
        if self.fin_juego and not self.mostrar_ronda3:
            mensaje = "¡HAS GANADO!" if self.gano else "HAS PERDIDO"

            texto = self.fuente_grande.render(mensaje, True, (255, 215, 0))
            self.pantalla.blit(
                texto,
                texto.get_rect(center=(configuracion.ancho // 2, 200))
            )

            self.rectangulo_boton = pygame.Rect(
                configuracion.ancho // 2 - 80,
                300,
                160,
                50
            )
            self.dibujar_boton("Volver a jugar", self.rectangulo_boton)

        pygame.display.flip()

    def ejecutar(self):
        # bucle principal
        while True:
            delta_tiempo = self.reloj.tick(configuracion.fps) / 1000

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if (
                    evento.type == pygame.KEYDOWN and
                    not self.fin_juego and
                    not self.mostrar_ronda3
                ):
                    if evento.key == pygame.K_SPACE and not self.bala:
                        self.disparar()

                if evento.type == pygame.MOUSEBUTTONDOWN and self.fin_juego:
                    if self.rectangulo_boton.collidepoint(evento.pos):
                        self.reiniciar_juego()

            teclas = pygame.key.get_pressed()     # controlar ángulo y potencia con las flechas

            if not self.fin_juego and not self.mostrar_ronda3:
                if teclas[pygame.K_UP]:
                    self.angulo = limitar(self.angulo + 60 * delta_tiempo, 10, 85)
                if teclas[pygame.K_DOWN]:
                    self.angulo = limitar(self.angulo - 60 * delta_tiempo, 10, 85)
                if teclas[pygame.K_RIGHT]:
                    self.potencia = limitar(self.potencia + 300 * delta_tiempo, 100, 1500)
                if teclas[pygame.K_LEFT]:
                    self.potencia = limitar(self.potencia - 300 * delta_tiempo, 100, 1500)

            self.actualizar(delta_tiempo)
            self.dibujar()

# ejecutar el juego
if __name__ == "__main__":
    funcionaminento_juego().ejecutar()