# Py-Duck-Invaders

import sys
from os.path import abspath, dirname
from random import choice

from pygame import *

# Definimos las rutas que usaremos posteriormente para acceder a los 'assets' del juego
BASE_PATH = abspath(dirname(__file__))  # Toma la ruta absoluta de los archivos pero sin el nombre del archivo
FONT_PATH = BASE_PATH + '/fonts/'
IMAGE_PATH = BASE_PATH + '/images/'
SOUND_PATH = BASE_PATH + '/sounds/'

# Definimos algunos colores que usaremos posteriormente
WHITE = (255, 255, 255)
GREEN = (152, 168, 112)
GREEN2 = (38, 219, 22)
YELLOW = (241, 255, 0)
BLUE = (107, 138, 187)
PURPLE = (212, 109, 146)
RED = (237, 28, 36)
GREY = (222, 207, 206)
# Establecemos dimensiones de la ventana y fuente tipográfica a usar
SCREEN = display.set_mode((800, 600))
FONT = FONT_PATH + 'space_invaders.ttf'

# Definimos los nombres de las imágenes en un array para luego acceder más cómodamente
IMG_NAMES = ['man', 'mystery',
             'enemy1_1', 'enemy1_2',
             'enemy2_1', 'enemy2_2',
             'enemy3_1', 'enemy3_2',
             'explosionblue', 'explosiongreen', 'explosionpurple',
             'laser', 'enemylaser']

# Con un For cargamos todas las imágenes para almacenarlas en el diccionario IMAGES, utilizando
# una función que recoge la ruta de la imagen y le añade la extensión .png, además le añadimos
# transparencia con convert.alpha
IMAGES = {name: image.load(IMAGE_PATH + '{}.png'.format(name)).convert_alpha()
          for name in IMG_NAMES}

BLOCKERS_POSITION = 450  # Altura de las barricadas
ENEMY_DEFAULT_POSITION = 65  # Posición inicial de los enemigos
ENEMY_MOVE_DOWN = 35  # Salto hacia abajo de los enemigos


# Clase que usaremos para nuestro héroe
class Man(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['man']  # Cargamos la imagen
        self.rect = self.image.get_rect(topleft=(375, 510))  #
        self.speed = 5

    # Función para gestionar el movimiento del héroe
    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.x > 1:  # Movimiento a la izq sin salir de la ventana
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < 760:  # Movimiento a la derecha sin salir de la ventana
            self.rect.x += self.speed
        game.screen.blit(self.image, self.rect)


# Clase para los proyectiles
class Bullet(sprite.Sprite):
    def __init__(self, xpos, ypos, direction, speed, filename, side):
        sprite.Sprite.__init__(self)
        self.image = IMAGES[filename]  # Definimos cuál será su imagen
        self.rect = self.image.get_rect(topleft=(xpos, ypos))  # La posición del disparo la recibimos por parámetro
        self.speed = speed  # Velocidad del proyectil
        self.direction = direction  # Dirección del proyectil
        self.side = side
        self.filename = filename

    # Función que actualiza la posición de los proyectiles
    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)
        self.rect.y += self.speed * self.direction  # El proyectil irá hacia arriba o hacia abajo según la dirección
        # Eliminamos el proyectil al salir de los límites de nuestra ventana
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()


# Clase para los enemigos (patitos)
class Enemy(sprite.Sprite):
    def __init__(self, row, column):
        sprite.Sprite.__init__(self)
        self.row = row
        self.column = column
        self.images = []  # Array para almacenar las imágenes de los patitos
        self.load_images()  # Cargamos las imágenes
        self.index = 0  # Índice para indicar la posición en el Array
        self.image = self.images[self.index]  # Establecemos la imagen con el Array y el índice
        self.rect = self.image.get_rect()

    # Función con la que recorremos el Array y que nos servirá para dibujar los patos que aún estén vivos.
    # Usaremos esta función posteriormente. Con ella definimos qué patitos habrán de dibujarse.
    # Esto lo conseguiremos recorriendo el array de enemigos vivos y llamando a esta función para cada uno de ellos.
    def toggle_image(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    # Con esta función cambiamos la dirección en la que miran los patitos cada vez que cambian de sentido.
    # Recorremos el Array de imágenes y volteamos horizontalmente cada imagen
    def change_direction(self):
        c = 0
        for img in self.images:
            img = transform.flip(img, True, False)
            self.images[c] = img
            c += 1

    # Esta función sirve para limpiar la pantalla y poder renderizar el siguiente frame
    def update(self, *args):
        game.screen.blit(self.image, self.rect)

    # Función que cargará nuestras imágenes (los enemigos)
    def load_images(self):
        images = {0: ['1_2', '1_1'],  # En esta línea tenemos un diccionario que usaremos
                  1: ['2_2', '2_1'],  # para cargar todas las distintas imágenes de nuestros patos
                  2: ['2_2', '2_1'],
                  3: ['3_1', '3_2'],
                  4: ['3_1', '3_2'],
                  }

        # Cargamos las dos imágenes (frames) de cada enemigo para conseguir la animación
        img1, img2 = (IMAGES['enemy{}'.format(img_num)] for img_num in
                      images[self.row])

        # Escalamos e incorporamos las imágenes previamente cargadas a un array que las almacenará
        self.images.append(transform.scale(img1, (40, 35)))
        self.images.append(transform.scale(img2, (40, 35)))


# Clase que usaremos para el movimiento de los patos
class EnemiesGroup(sprite.Group):
    def __init__(self, columns, rows):
        sprite.Group.__init__(self)
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns  # Esta será la cantidad de columnas de patitos que generaremos
        self.rows = rows  # Esta será la cantidad de filas de patitos que generaremos
        self.leftAddMove = 0
        self.rightAddMove = 0
        self.moveTime = 300  # Tiempo entre saltitos de los enemigos. Default -> 600
        self.direction = 1
        self.rightMoves = 30  # Cantidad de saltos que los patos darán antes de cambiar de sentido (hacia la derecha)
        self.leftMoves = 30  # Cantidad de saltos que los patos darán antes de cambiar de sentido (hacia la izquierda)
        self.moveNumber = 15  # Cantidad de saltos que los patos han dado. Inicialmente es 15 porque aparecen en mitad
        # de la pantalla (y han de llegar a 30)
        self.timer = time.get_ticks()  # Temporizador que usaremos para controlar el movimiento
        self.bottom = game.enemyPosition + ((rows - 1) * 45) + 35  # Esta variable la usaremos para saber cuándo los
        # patos han llegado al suelo
        self._aliveColumns = list(range(columns))  # En esta variable almacenaremos las columnas de patos que siguen
        # vivas. Nos hará falta para saber cuándo deberán cambiar de sentido
        self._leftAliveColumn = 0  # Esta variable, junto con su homónima declarada en la línea siguiente será un
        self._rightAliveColumn = columns - 1  # complemento de la anterior. Esto es, tendrán el mismo propósito.

    # Con esta función, cada vez que ejecutemos esta función se actualizarán los patos.
    # Concretamente controlamos el movimiento.
    def update(self, current_time):
        # Utilizamos el temporizador de la clase para mover los patos cada vez que llegue al tiempo que previamente
        # hemos establecido en self.moveTime
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:  # Comprobamos si los patos van hacia la derecha, en cuyo caso los moveremos
                # en dicha dirección
                max_move = self.rightMoves + self.rightAddMove
            else:  # Si los patos van hacia la izquierda, los movemos de la misma forma
                max_move = self.leftMoves + self.leftAddMove

            # Controlamos cuándo los patos llegan al final de la pantalla y han de cambiar de sentido
            if self.moveNumber >= max_move:
                self.leftMoves = 30 + self.rightAddMove  # Reseteamos las variables que controlan la cantidad de
                self.rightMoves = 30 + self.leftAddMove  # saltitos en ambas direcciones
                self.direction *= -1  # También podemos hacer (self.direction = -self.direction). Con esto conseguimos
                # el cambio de dirección de los patos.
                self.moveNumber = 0  # Reseteamos el número de saltitos que han dado los patos
                self.bottom = 0  # Reseteamos la variable que controla cuándo los patos llegan al suelo. La
                # actualizaremos en el siguiente bucle for.

                # Recorremos todos los enemigos restantes
                for enemy in self:
                    # Para cada enemigo vivo, llamamos a la función change_direction para hacerlos cambiar de sentido
                    enemy.change_direction()
                    enemy.rect.y += ENEMY_MOVE_DOWN
                    enemy.toggle_image()  # Llamamos a la función toggle_image() para dibujar solo los patos vivos
                    if self.bottom < enemy.rect.y + 35:  # Comprobamos cuál es la última línea de patos
                        self.bottom = enemy.rect.y + 35  # Guardamos la altura de la misma en la variable self.bottom
            else:
                velocity = 10 if self.direction == 1 else -10  # Ajustamos la velocidad dependiendo del sentido
                for enemy in self:
                    enemy.rect.x += velocity  # Movemos los patitos de lugar en el eje x según la velocidad
                    enemy.toggle_image()  # Llamamos a la función toggle_image() para dibujar solo los patos vivos
                self.moveNumber += 1  # Añadimos +1 a la cantidad de saltos que han dado los patos

            self.timer += self.moveTime  # Actualizamos el temporizador para el siguiente saltito

    # Función que usaremos para activar a todos los enemigos uno por uno
    def add_internal(self, *sprite):
        super(EnemiesGroup, self).add_internal(*sprite)  # Con el operador * pasamos la tupla entera como argumento
        for s in sprite:
            self.enemies[s.row][s.column] = s  # Almacenamos los enemigos en su array correspondiente

    # De la misma forma que la función anterior, con esta eliminaremos los enemigos que debamos
    def remove_internal(self, *sprites):
        super(EnemiesGroup, self).remove_internal(*sprites)
        for s in sprites:
            self.kill(s)  # Utilizamos la función kill que definiremos más adelante
        self.update_speed()  # Utilizamos la función update que definiremos más adelante

    # Con este método calculamos si la columna que pasemos como parámetro esta completamente eliminada
    # https://stackoverflow.com/questions/19389490/how-do-pythons-any-and-all-functions-work
    def is_column_dead(self, column):
        return not any(self.enemies[row][column]  # Utilizamos any junto con una negación para dicho propósito (any
                       for row in range(self.rows))  # devolverá True si encuentra un elemento, pero al negarlo con not
        # devolverá False (es decir, columna no muerta))

    # Con esta función elegimos un pato aleatorio de la fila inferior, el cual efectuará un disparo posteriormente
    def random_bottom(self):
        col = choice(self._aliveColumns)  # choice(seq) nos devuelve un elemento aleatorio de la tupla que pasemos como
        # parámetro, en este caso las columnas vivas
        col_enemies = (self.enemies[row - 1][col]
                       for row in range(self.rows, 0, -1))  # Almacenamos todos los enemigos restantes
        # de la columna elegida
        return next((en for en in col_enemies if en is not None), None)  # Devolvemos el pato en la posición inferior

    # Función con la que ajustaremos la velocidad de movimiento según vayan quedado menos patos con vida
    def update_speed(self):
        if len(self) == 1:  # Cuando quede 1 sólo pato aumentaremos la velocidad al máximo
            self.moveTime = 100
        elif len(self) <= 10:  # Cuando queden 10 patos o menos aumentaremos la velocidad
            self.moveTime = 200

    # Función con la que eliminaremos los patos muertos
    def kill(self, enemy):
        self.enemies[enemy.row][enemy.column] = None
        is_column_dead = self.is_column_dead(
            enemy.column)  # Con la función is_column_dead identificamos si hay columnas
        # con todos sus patos eliminados
        if is_column_dead:  # Si la columna está completamente eliminada, la resta de las columnas en las que aún
            self._aliveColumns.remove(enemy.column)  # queden patos vivos

        # Con el siguiente if y elif controlamos cuándo una columna lateral ha sido completamente eliminada En tal
        # caso, sumaremos o restaremos 1 a estas columnas respectivamente y añadiremos una cantidad de saltitos extra
        # para que los patos sigan avanzando hasta el final de la pantalla Para ello usamos un bucle que comprueba
        # cuando alguna de las columnas laterales ha sido completamente eliminada hasta que las columnas laterales
        # contengan enemigos
        if enemy.column == self._rightAliveColumn:
            while self._rightAliveColumn > 0 and is_column_dead:
                self._rightAliveColumn -= 1
                self.rightAddMove += 5
                is_column_dead = self.is_column_dead(self._rightAliveColumn)

        elif enemy.column == self._leftAliveColumn:
            while self._leftAliveColumn < self.columns and is_column_dead:
                self._leftAliveColumn += 1
                self.leftAddMove += 5
                is_column_dead = self.is_column_dead(self._leftAliveColumn)


# Clase para las barricadas que recibe parámetros de la función make_blockers que esta dentro de la clase SpaceInvaders
class Blocker(sprite.Sprite):
    def __init__(self, size, color, row, column):  # (self, 10, GREEN2, row, column)
        sprite.Sprite.__init__(self)
        self.height = size  # Altura en píxeles
        self.width = size  # Ancho en píxeles
        self.color = color
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

    # Función que actualiza las barricadas
    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)


# Clase para el X-Wing Fighter
class Mystery(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['mystery']  # Asignamos la imagen de la nave del diccionario que creamos al principio
        self.image = transform.scale(self.image, (70, 39))  # la reescalamos
        self.rect = self.image.get_rect(
            topleft=(-80, 30))  # Definimos el rectángulo y sus coordenadas para el movimiento
        self.row = 5
        self.moveTime = 25000  # Tiempo que tarda la nave en volver a aparecer
        self.direction = 1  # Dirección inicial de la nave
        self.timer = time.get_ticks()  # Temporizador para actualizar el movimiento de la nave
        self.mysteryEntered = mixer.Sound(SOUND_PATH + 'mysteryentered.wav')  # Asignamos el sonido para la nave
        self.mysteryEntered.set_volume(0.3)  # Asignamos el volumen al que se reproducirá
        self.playSound = True

    # Función que actualiza el X-Wing Fighter. Se encarga principalmente de controlar su movimiento
    def update(self, keys, currentTime, *args):
        resetTimer = False
        passed = currentTime - self.timer

        # Cuando passed sea mayor que self.moveTime actualizaremos nuestra nave
        if passed > self.moveTime:
            # Cuando la nave entra en la pantalla reproducimos el sonido de entrada
            if (self.rect.x < 0 or self.rect.x > 800) and self.playSound:
                self.mysteryEntered.play()
                self.playSound = False
            # Cuando la nave esté dentro de la pantalla reproducimos el sonido elegido
            # que se irá desvaneciendo a lo largo de 4 segundos (4000 milisegundos)
            # Los dos siguientes if hacen lo mismo con la diferencia de la dirección
            # Dependiendo del sentido (self.direction) moveremos la nave hacia la izquierda o la derecha
            if self.rect.x < 840 and self.direction == 1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x += 2
                game.screen.blit(self.image, self.rect)
            if self.rect.x > -100 and self.direction == -1:
                self.mysteryEntered.fadeout(4000)
                self.rect.x -= 2
                game.screen.blit(self.image, self.rect)

        # Los dos siguientes if nos indican cuándo se sale de la pantalla (por la izquierda o la derecha)
        # Cuando se cumple dicha condición, cambiamos la dirección para cuando vuelva a aparecer y
        # reproducimos el sonido asignado
        if self.rect.x > 830:
            self.playSound = True
            self.direction = -1
            resetTimer = True
        if self.rect.x < -90:
            self.playSound = True
            self.direction = 1
            resetTimer = True  # Reseteamos el temporizador

        # En el caso de que el temporizador llegue al tiempo necesario para que se mueva y resetTimer sea True
        # volvemos a establecer el temporizador al tiempo actual y volteamos la imagen
        if passed > self.moveTime and resetTimer:
            self.timer = currentTime
            self.image = transform.flip(self.image, True, False)  # Voltea la imagen sobre su eje horizontal


# Clase que usamos para gestionar la animación que salta al acertar a un pato
class EnemyExplosion(sprite.Sprite):
    def __init__(self, enemy, *groups):
        super(EnemyExplosion, self).__init__(*groups)
        self.image = transform.scale(self.get_image(enemy.row), (40, 35))  # Llamamos a la función para la imagen y
        # la escalamos
        self.image2 = transform.scale(self.get_image(enemy.row), (50, 45))  # La misma imagen de la explosión pero
        # reescalada un poco más grande, esto crea un ligero efecto de expansión de la explosión
        self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))  # Definimos el rectángulo y sus
        # coordenadas
        self.timer = time.get_ticks()  # Temporizador para actualizar cuando pasar de image a image2

    # Con esta función cargamos las imágenes según la fila en una lista y nos devolverá la imagen que necesitemos
    # según la fila y añadiendo "explosion" delante para que coincida con el nombre de las imágenes
    @staticmethod
    def get_image(row):
        img_colors = ['purple', 'blue', 'blue', 'green', 'green']
        return IMAGES['explosion{}'.format(img_colors[row])]

    # Con esta función controlamos la frecuencia con la que van a dibujarse las imágenes apoyándonos en el temporizador
    # Si la resta es menos de 100 ms se dibujará una imagen, si es menos de 200 ms otra, y si han pasado más de 400 ms
    # se borra de la pantalla
    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 100:
            game.screen.blit(self.image, self.rect)  # Dibujamos en pantalla la primera imagen
        elif passed <= 200:
            game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))  # Restamos 6 a X/Y para corregir la
            # posición y que coincida centrada con la primera
        elif 400 < passed:
            self.kill()


# Clase para la animación de derribo (la puntuación) del X-Wing Fighter
class MysteryExplosion(sprite.Sprite):
    def __init__(self, mystery, score, *groups):  # Con el operador * pasamos la tupla entera
        super(MysteryExplosion, self).__init__(*groups)
        self.text = Text(FONT, 20, str(score), WHITE,
                         mystery.rect.x + 20, mystery.rect.y + 6)  # Al derribar la nave mostramos el texto con la
        # puntuación recibida, pasamos las coordenadas x+20 e y+6 para que coincidan con el sprite de la nave
        self.timer = time.get_ticks()

    # Igual que con las explosiones de los patos, esta función sirve para controlar cuando dibujar o retirar el texto
    # con la puntuación que ha dado el X-Wing Fighter con ayuda del temporizador
    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 200 or 400 < passed <= 600:
            self.text.draw(game.screen)
        elif 600 < passed:
            self.kill()


# Clase para la animación de muerte del cazador
class ManDeath(sprite.Sprite):
    def __init__(self, man, *groups):
        super(ManDeath, self).__init__(*groups)  # Pasamos la tupla al completo con el operador *
        self.image = IMAGES['man']  # Definimos que imagen coger del diccionario de imágenes
        self.rect = self.image.get_rect(topleft=(man.rect.x, man.rect.y))  # Coordenadas para dibujar el rectángulo
        self.timer = time.get_ticks()  # Temporizador

    # Con esta función controlamos cuando dibujar y cuando retirar la animación de muerte del cazador
    # Igual que con la explosión de los patos, esta función sirve para controlar cuando dibujar o retirar la animación
    # de muerte del cazador con ayuda del temporizador
    def update(self, current_time, *args):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            game.screen.blit(self.image, self.rect)
        elif 900 < passed:
            self.kill()


# Con esta clase colocamos la imagen del cazador redimensionada a 23x23 en las coordenadas X e Y que recibe por
# parámetro la función __init__
class Life(sprite.Sprite):
    def __init__(self, xpos, ypos):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['man']  # Definimos que imagen coger del diccionario de imágenes
        self.image = transform.scale(self.image, (23, 23))  # Redimensionamos la imagen
        self.rect = self.image.get_rect(topleft=(xpos, ypos))  # Definimos el rectángulo y sus coordenadas

    # Con esta función pintamos las 3 imágenes para las vidas del jugador
    def update(self, *args):
        game.screen.blit(self.image, self.rect)  # Pintamos el rectángulo en pantalla


# Con esta clase colocamos los textos del HUD en pantalla.
# Pasamos por parámetro la fuente a usar, tamaño, el mensaje, el color y las posiciones X e Y
class Text(object):
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    # Con esta función dibujamos en pantalla los textos
    def draw(self, surface):
        surface.blit(self.surface, self.rect)


# Esta es la CLASE PRINCIPAL, desde la que controlamos cada elemento y llamamos a todas las funciones previas
class SpaceInvaders(object):
    def __init__(self):
        mixer.pre_init(44100, -16, 1, 4096)  # Cargamos el módulo de pygame Mixer para reproducir sonidos
        init()
        self.clock = time.Clock()
        self.caption = display.set_caption('Py-Duck Invaders')  # Título de la ventana
        self.screen = SCREEN
        self.background = image.load(IMAGE_PATH + 'Fondo.jpg').convert()  # Cargamos la imagen de fondo
        self.background = transform.scale(self.background, (800, 600))  # Y la ajustamos al tamaño de la ventana
        self.startGame = False
        self.mainScreen = True
        self.gameOver = False
        self.enemyPosition = ENEMY_DEFAULT_POSITION  # Contador para la posición de inicio de los patos (la
        # incrementamos en cada nueva ronda)

        # Establecemos los textos y puntuaciones de cada pato en el menú principal
        self.titleText = Text(FONT, 50, 'Py-Duck Invaders', WHITE, 134, 155)
        self.titleText2 = Text(FONT, 25, 'Pulsa una tecla para empezar', WHITE, 170, 225)
        self.gameOverText = Text(FONT, 50, 'Game Over', WHITE, 250, 270)
        self.nextRoundText = Text(FONT, 50, 'Next Round', WHITE, 240, 270)
        self.enemy1Text = Text(FONT, 25, '   =   10 pts', GREEN, 368, 270)
        self.enemy2Text = Text(FONT, 25, '   =   20 pts', BLUE, 368, 320)
        self.enemy3Text = Text(FONT, 25, '   =   30 pts', PURPLE, 368, 370)
        self.enemy4Text = Text(FONT, 25, '   =   ?????', WHITE, 368, 420)
        self.scoreText = Text(FONT, 20, 'Puntuacion', WHITE, 5, 5)
        self.livesText = Text(FONT, 20, 'Vidas ', WHITE, 640, 5)

        # Pasamos a la clase Life las coordenadas para que nos dibuje las 3 vidas ahí
        self.life1 = Life(715, 3)
        self.life2 = Life(742, 3)
        self.life3 = Life(769, 3)
        self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)  # Agrupamos las 3 vidas en un contenedor

    # Función con la que reseteamos el juego a los valores iniciales
    def reset(self, score):
        self.player = Man()
        self.playerGroup = sprite.Group(self.player)  # Agrupamos los sprites del cazador
        self.explosionsGroup = sprite.Group()  # Agrupamos los sprites de las explosiones
        self.bullets = sprite.Group()  # Agrupamos los sprites de las balas
        self.mysteryShip = Mystery()
        self.mysteryGroup = sprite.Group(self.mysteryShip)  # Agrupamos los sprites del X-Wing Fighter
        self.enemyBullets = sprite.Group()  # Agrupamos los sprites de los "disparos" de los patos
        self.make_enemies()  # Llamada a la función que se encarga de generar las matriz de patos
        self.allSprites = sprite.Group(self.player, self.enemies, self.livesGroup, self.mysteryShip)  # Agrupamos todos
        self.keys = key.get_pressed()  # Variable para controlar las teclas presionadas o liberadas
        self.timer = time.get_ticks()  # Temporizador en ms
        self.noteTimer = time.get_ticks()  # Temporizador en ms para los sonidos
        self.manTimer = time.get_ticks()  # Temporizador en ms para el cazador
        self.score = score
        self.create_audio()  # Llamada a la función que crea los archivos de sonido
        self.makeNewMan = False
        self.manAlive = True

    # Función para crear las 4 barricadas, recibirá el número de bloques por parámetro
    def make_blockers(self, number):
        blockerGroup = sprite.Group()  # Agrupamos los bloques en un contenedor
        # Para cada bloque creamos una matriz de 4 filas y de 9 columnas
        for row in range(4):
            for column in range(9):
                blocker = Blocker(10, GREEN2, row, column)  # Pasamos los parámetros a la clase Blocker
                blocker.rect.x = 50 + (200 * number) + (column * blocker.width)  # Separamos los bloques unos de otros
                blocker.rect.y = BLOCKERS_POSITION + (row * blocker.height)  # Altura de nºfilas*tamaño de cuadrito
                blockerGroup.add(blocker)  # Y lo agrupamos
        return blockerGroup

    # Con un For cargamos todas los nombres de los archivos de sonido para almacenarlos en el diccionario sounds,
    # utilizando una función que recoge la ruta del archivo de sonido y le añade la extensión .wav
    def create_audio(self):
        self.sounds = {}  # Creamos el diccionario
        for sound_name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled', 'manexplosion']:
            self.sounds[sound_name] = mixer.Sound(SOUND_PATH + '{}.wav'.format(sound_name))
            self.sounds[sound_name].set_volume(0.2)  # Establecemos el volumen en 0.2 para estos sonidos

        # Creamos un array con nuestros 4 sonidos de avance de los patos
        self.musicNotes = [mixer.Sound(SOUND_PATH + '{}.wav'.format(i)) for i in range(4)]
        for sound in self.musicNotes:  # Recorremos el array anterior para
            sound.set_volume(0.5)  # establecer el volumen de los 4 sonidos a 0.5

        # Inicializamos el índice de las notas a 0; usaremos este campo en la próxima función para determinar qué
        # nota sonará
        self.noteIndex = 0

    # Reproducimos nuestras 4 notas cuando corresponda
    def play_main_music(self, currentTime):
            # Establecemos qué nota sonará, de acuerdo a nuestro índice
            self.note = self.musicNotes[self.noteIndex]

            # Si no hemos llegado a nuestra última nota (índice 3), aumentamos el índice para la siguiente ejecución
            if self.noteIndex < 3:
                self.noteIndex += 1
            else:  # Si llegamos al índice 3 volvemos a estrablecer el índice a 0
                self.noteIndex = 0

            # Reproducimos la nota en cuestión
            self.note.play()

            # Establecemos el temporizador que controlará cuándo suena la nota para que esté sincronizado con el avance
            # de los patos
            self.noteTimer += self.enemies.moveTime

    # Con esta función devolvemos un boolean, que será true si cerramos nuestro juego o si pulsamos alguna teclado
    # Nos será útil posteriormente para controlal el input por teclado
    @staticmethod
    def should_exit(evt):
        # type: (pygame.event.EventType) -> bool
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    # Controlamos el input del teclado
    def check_input(self):
        self.keys = key.get_pressed()  # Recogemos qué tecla ha sido pulsada
        for e in event.get():  # Iteramos sobre los eventos
            if self.should_exit(e):  # Si cerramos nuestro juego, acabamos con la ejecución del programa
                sys.exit()
            if e.type == KEYDOWN:  # Controlamos si pulsamos alguna tecla
                if e.key == K_SPACE:  # Controlamos si la tecla que pulsamos es la tecla "Espacio"
                    # Controlamos que no haya ninguna bala creada y que estemos vivos para poder disparar
                    if len(self.bullets) == 0 and self.manAlive:
                        # Con el siguiente if, else controlamos el tipo de disparo:
                        # Si nuestra puntuación es menor que 1000 disparamos una bala,
                        # de lo contrario disparamos 2
                        if self.score < 1000:
                            # Creamos la bala en la posición del jugador
                            bullet = Bullet(self.player.rect.x + 19.5,
                                            self.player.rect.y + 5, -1,
                                            15, 'laser', 'center')
                            self.bullets.add(bullet)  # Añadimos la bala creada a nuestro array de balas
                            self.allSprites.add(self.bullets)  # Añadimos el array a nuestro array de sprites
                            self.sounds['shoot'].play()  # Reproducimos el sonido de disparar
                        else:
                            # En el else repetimos el proceso del if, pero con dos balas esta vez
                            leftbullet = Bullet(self.player.rect.x + 8,
                                                self.player.rect.y + 5, -1,
                                                15, 'laser', 'left')
                            rightbullet = Bullet(self.player.rect.x + 38,
                                                 self.player.rect.y + 5, -1,
                                                 15, 'laser', 'right')
                            self.bullets.add(leftbullet)
                            self.bullets.add(rightbullet)
                            self.allSprites.add(self.bullets)
                            self.sounds['shoot2'].play()

    # Función que se encarga de generar el array de patos
    def make_enemies(self):
        enemies = EnemiesGroup(10, 5)  # Creamos el grupo de enemigos: será un grupo de 10 columnas y 5 filas
        # Para cada una de esas columnas y filas generamos un pato
        for row in range(5):
            for column in range(10):
                enemy = Enemy(row, column)
                enemy.rect.x = 157 + (column * 50)  # Establecemos la coordenada X, según la columna en la que se genere
                enemy.rect.y = self.enemyPosition + (row * 45)  # Hacemos lo mismo para la coordenada Y según la fila
                enemies.add(enemy)  # Añadimos el enemigo creado al array de enemigos

        # Definimos el miembro de clase como el grupo de enemigos que creamos al principio de la función y modificamos
        # durante la misma
        self.enemies = enemies

    # Creamos la función con la que controlaremos el disparo de los patos
    def make_enemies_shoot(self):
        # Cada vez que el temporizador llege a 700 (0,7 segundos) algún pato disparará, siempre y
        # cuando quede alguno vivo
        if (time.get_ticks() - self.timer) > 700 and self.enemies:
            # Elegimos el enemigo que disparará con la función que creamos previamente
            enemy = self.enemies.random_bottom()
            # Creamos una bala y la añadimos a nuestro array de balas enemigos
            self.enemyBullets.add(
                Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 1, 5, 'enemylaser', 'center'))
            self.allSprites.add(self.enemyBullets)  # Añadimos el array de balas enemigas al array de todos los sprites
            self.timer = time.get_ticks()  # Reestablecemos el temporizador

    # Función con la que definimos las puntuaciones de los patos y la nave sorpresa y las añadimos a un diccionario
    def calculate_score(self, row):
        # Creamos un diccionario con las posibles puntuaciones
        # El elemento con clave 5 será para el enemigo especial,
        # que elegirá un valor aleatorio entre los 4 del array
        scores = {0: 30,
                  1: 20,
                  2: 20,
                  3: 10,
                  4: 10,
                  5: choice([50, 100, 150, 300])
                  }
        # Elegimos la puntición que obtendremos, según lo que pasemos com parámetro
        score = scores[row]
        self.score += score  # Sumamos la puntuación elegida a nuestro marcador
        return score  # Devolcemos la puntuación obtenida

    # Insertamos las imágenes correspondientes en el menú principal
    def create_main_menu(self):
        self.enemy1 = IMAGES['enemy3_1']  # Elegimos la imagen del pato verde
        self.enemy1 = transform.scale(self.enemy1, (40, 40))  # Y la escalamos a 40x40
        self.enemy2 = IMAGES['enemy2_2']  # Elegimos la imagen del pato azul
        self.enemy2 = transform.scale(self.enemy2, (40, 40))  # Y la escalamos a 40x40
        self.enemy3 = IMAGES['enemy1_2']  # Elegimos la imagen del pato rojo
        self.enemy3 = transform.scale(self.enemy3, (40, 40))  # Y la escalamos a 40x40
        self.enemy4 = IMAGES['mystery']  # Elegimos la imagen del X-Wing Fighter
        self.enemy4 = transform.scale(self.enemy4, (70, 39))  # Y la escalamos a 70x39
        self.screen.blit(self.enemy1, (318, 270))  # Dibujamos en pantalla las imágenes en sus coordenadas
        self.screen.blit(self.enemy2, (318, 320))
        self.screen.blit(self.enemy3, (318, 370))
        self.screen.blit(self.enemy4, (299, 420))

    # Función para comprobar las colisiones
    def check_collisions(self):
        ####################################################################################################################
        sprite.groupcollide(self.bullets, self.enemyBullets, True, True)

        for enemy in sprite.groupcollide(self.enemies, self.bullets, True, True).keys():
            self.sounds['invaderkilled'].play()
            self.calculate_score(enemy.row)
            EnemyExplosion(enemy, self.explosionsGroup)
            self.gameTimer = time.get_ticks()

        for mystery in sprite.groupcollide(self.mysteryGroup, self.bullets, True, True).keys():
            mystery.mysteryEntered.stop()
            self.sounds['mysterykilled'].play()
            score = self.calculate_score(mystery.row)
            MysteryExplosion(mystery, score, self.explosionsGroup)
            newShip = Mystery()
            self.allSprites.add(newShip)
            self.mysteryGroup.add(newShip)

        for player in sprite.groupcollide(self.playerGroup, self.enemyBullets, True, True).keys():
            if self.life3.alive():
                self.life3.kill()
            elif self.life2.alive():
                self.life2.kill()
            elif self.life1.alive():
                self.life1.kill()
            else:
                self.gameOver = True
                self.startGame = False
            self.sounds['manexplosion'].play()
            ManDeath(player, self.explosionsGroup)
            self.makeNewMan = True
            self.manTimer = time.get_ticks()
            self.manAlive = False

        if self.enemies.bottom >= 540:
            sprite.groupcollide(self.enemies, self.playerGroup, True, True)
            if not self.player.alive() or self.enemies.bottom >= 600:
                self.gameOver = True
                self.startGame = False

        sprite.groupcollide(self.bullets, self.allBlockers, True, True)
        sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
        if self.enemies.bottom >= BLOCKERS_POSITION:
            sprite.groupcollide(self.enemies, self.allBlockers, False, True)

    def create_new_man(self, createMan, currentTime):
        if createMan and (currentTime - self.manTimer > 900):
            self.player = Man()
            self.allSprites.add(self.player)
            self.playerGroup.add(self.player)
            self.makeNewMan = False
            self.manAlive = True

    def create_game_over(self, currentTime):
        self.screen.blit(self.background, (0, 0))
        passed = currentTime - self.timer
        if passed < 750:
            self.gameOverText.draw(self.screen)
        elif 750 < passed < 1500:
            self.screen.blit(self.background, (0, 0))
        elif 1500 < passed < 2250:
            self.gameOverText.draw(self.screen)
        elif 2250 < passed < 2750:
            self.screen.blit(self.background, (0, 0))
        elif passed > 3000:
            self.mainScreen = True

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    def main(self):
        while True:
            if self.mainScreen:
                self.screen.blit(self.background, (0, 0))
                self.titleText.draw(self.screen)
                self.titleText2.draw(self.screen)
                self.enemy1Text.draw(self.screen)
                self.enemy2Text.draw(self.screen)
                self.enemy3Text.draw(self.screen)
                self.enemy4Text.draw(self.screen)
                self.create_main_menu()
                for e in event.get():
                    if self.should_exit(e):
                        sys.exit()
                    if e.type == KEYUP:
                        # Creamos los bloques solo en una nueva partida, no en cada nueva ronda
                        self.allBlockers = sprite.Group(self.make_blockers(0),
                                                        self.make_blockers(1),
                                                        self.make_blockers(2),
                                                        self.make_blockers(3))
                        self.livesGroup.add(self.life1, self.life2, self.life3)
                        self.reset(0)
                        self.startGame = True
                        self.mainScreen = False

            elif self.startGame:
                if not self.enemies and not self.explosionsGroup:
                    currentTime = time.get_ticks()
                    if currentTime - self.gameTimer < 3000:
                        self.screen.blit(self.background, (0, 0))
                        self.scoreText2 = Text(FONT, 20, str(self.score), GREEN, 160, 5)
                        self.scoreText.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        self.nextRoundText.draw(self.screen)
                        self.livesText.draw(self.screen)
                        self.livesGroup.update()
                        self.check_input()
                    if currentTime - self.gameTimer > 3000:
                        # Mueve a los patos más cerca del suelo
                        self.enemyPosition += ENEMY_MOVE_DOWN
                        self.reset(self.score)
                        self.gameTimer += 3000
                else:
                    currentTime = time.get_ticks()
                    self.play_main_music(currentTime)
                    self.screen.blit(self.background, (0, 0))
                    self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(FONT, 20, str(self.score), GREEN, 160, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.livesText.draw(self.screen)
                    self.check_input()
                    self.enemies.update(currentTime)
                    self.allSprites.update(self.keys, currentTime)
                    self.explosionsGroup.update(currentTime)
                    self.check_collisions()
                    self.create_new_man(self.makeNewMan, currentTime)
                    self.make_enemies_shoot()

            elif self.gameOver:
                currentTime = time.get_ticks()
                # Reseteamos la posición inicial de los patos
                self.enemyPosition = ENEMY_DEFAULT_POSITION
                self.create_game_over(currentTime)

            display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    game = SpaceInvaders()
    game.main()
