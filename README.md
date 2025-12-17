Tiro Parabólico – Juego en Python

Descripción:
Juego de disparos en 2D donde controlas un cañón para acertar a una diana móvil. El juego simula física realista de proyectiles, incluyendo gravedad y trayectoria parabólica. Incluye animaciones de proyectiles, estelas, predicción de la trayectoria y pantallas especiales según la ronda.

Características:

Física realista: gravedad, velocidad inicial y ángulo de disparo.

Diana móvil: posición aleatoria y movimiento sinusoidal.

Estela del proyectil: visualización de la trayectoria pasada del proyectil.

Predicción de trayectoria: línea discontinua que muestra la ruta del disparo.

Control de cañón: ajustar ángulo y potencia con las flechas del teclado.

Rondas y objetivos: 3 rondas, cada una con una diana diferente.

Pantallas especiales: imagen especial en la tercera ronda.

Sistema de intentos: 3 intentos por ronda antes de perder.

Sonidos: efectos de victoria y derrota.

Interfaz sencilla: visualización de ronda actual, intentos y botones interactivos.

Controles:

Flechas arriba / abajo: ajustar el ángulo del cañón (10° – 85°).

Flechas izquierda / derecha: ajustar la potencia del disparo (100 – 1500).

Espacio: disparar el proyectil.

Click en botón “Volver a jugar”: reinicia el juego al finalizar.

Requisitos:

Python 3.8+

Pygame
 (pip install pygame)

Archivos adicionales necesarios:

victory.wav → sonido de victoria

defeat.wav → sonido de derrota

round3.png → imagen especial de la tercera ronda

Estructura del código:

configuracion: parámetros generales del juego (ancho, alto, FPS, gravedad, título).

colores: paleta de colores para fondo, elementos y botones.

fisica: medidas y posiciones de los objetos del juego (cañón, proyectil, diana).

proyectil: clase que representa cada proyectil, incluyendo actualización de posición y estela.

diana: clase que representa la diana móvil, con detección de impacto.

funcionaminento_juego: clase principal del juego que maneja la lógica, actualización, dibujo y ejecución.

Instalación y ejecución

Clonar o descargar el repositorio.

Instalar Pygame:

pip install pygame


Colocar los archivos victory.wav, defeat.wav y round3.png en la misma carpeta que el script.

Ejecutar el juego:

python nombre_del_archivo.py

Notas:

El juego está optimizado para 900x600 píxeles.

Puedes ajustar la gravedad, potencia y número de rondas modificando la clase configuracion.

La tercera ronda muestra una imagen especial por 3 segundos antes de continuar con la dinámica normal.
