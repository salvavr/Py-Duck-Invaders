# Py-Duck-Invaders

from pygame import *
import sys
from os.path import abspath, dirname
from random import choice

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
        self.height = size
        self.width = size
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
        self.image = transform.scale(self.image, (70, 60))  # la reescalamos
        self.rect = self.image.get_rect(
            topleft=(-80, 25))  # Definimos el rectángulo y sus coordenadas para el movimiento
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

    @staticmethod
    # Con esta función cargamos las imágenes según la fila en una lista y nos devolverá la imagen que necesitemos
    # según la fila y añadiendo "explosion" delante
    def get_image(row):
        img_colors = ['purple', 'blue', 'blue', 'green', 'green']
        return IMAGES['explosion{}'.format(img_colors[row])]

# Con esta función
    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 100:
            game.screen.blit(self.image, self.rect)
        elif passed <= 200:
            game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
        elif 400 < passed:
            self.kill()


class MysteryExplosion(sprite.Sprite):
    def __init__(self, mystery, score, *groups):
        super(MysteryExplosion, self).__init__(*groups)
        self.text = Text(FONT, 20, str(score), WHITE,
                         mystery.rect.x + 20, mystery.rect.y + 6)
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 200 or 400 < passed <= 600:
            self.text.draw(game.screen)
        elif 600 < passed:
            self.kill()


class ManDeath(sprite.Sprite):
    def __init__(self, ship, *groups):
        super(ManDeath, self).__init__(*groups)
        self.image = IMAGES['man']
        self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            game.screen.blit(self.image, self.rect)
        elif 900 < passed:
            self.kill()


class Life(sprite.Sprite):
    def __init__(self, xpos, ypos):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['man']
        self.image = transform.scale(self.image, (23, 23))
        self.rect = self.image.get_rect(topleft=(xpos, ypos))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Text(object):
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)


class SpaceInvaders(object):
    def __init__(self):
        mixer.pre_init(44100, -16, 1, 4096)
        init()
        self.clock = time.Clock()
        self.caption = display.set_caption('Py-Duck Invaders')
        self.screen = SCREEN
        self.background = image.load(IMAGE_PATH + 'Fondo.jpg').convert()  # Cargamos la imagen de fondo
        self.background = transform.scale(self.background, (800, 600))  # Y la ajustamos al tamaño de la ventana
        self.startGame = False
        self.mainScreen = True
        self.gameOver = False
        # Counter for enemy starting position (increased each new round)
        self.enemyPosition = ENEMY_DEFAULT_POSITION
        self.titleText = Text(FONT, 50, 'Py-Duck Invaders', WHITE, 134, 155)
        self.titleText2 = Text(FONT, 25, 'Pulsa una tecla para empezar', WHITE,
                               170, 225)
        self.gameOverText = Text(FONT, 50, 'Game Over', WHITE, 250, 270)
        self.nextRoundText = Text(FONT, 50, 'Next Round', WHITE, 240, 270)
        self.enemy1Text = Text(FONT, 25, '   =   10 pts', GREEN, 368, 270)
        self.enemy2Text = Text(FONT, 25, '   =   20 pts', BLUE, 368, 320)
        self.enemy3Text = Text(FONT, 25, '   =   30 pts', PURPLE, 368, 370)
        self.enemy4Text = Text(FONT, 25, '   =   ?????', WHITE, 368, 420)
        self.scoreText = Text(FONT, 20, 'Puntuacion', WHITE, 5, 5)
        self.livesText = Text(FONT, 20, 'Vidas ', WHITE, 640, 5)

        self.life1 = Life(715, 3)
        self.life2 = Life(742, 3)
        self.life3 = Life(769, 3)
        self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)

    def reset(self, score):
        self.player = Man()
        self.playerGroup = sprite.Group(self.player)
        self.explosionsGroup = sprite.Group()
        self.bullets = sprite.Group()
        self.mysteryShip = Mystery()
        self.mysteryGroup = sprite.Group(self.mysteryShip)
        self.enemyBullets = sprite.Group()
        self.make_enemies()
        self.allSprites = sprite.Group(self.player, self.enemies,
                                       self.livesGroup, self.mysteryShip)
        self.keys = key.get_pressed()

        self.timer = time.get_ticks()
        self.noteTimer = time.get_ticks()
        self.shipTimer = time.get_ticks()
        self.score = score
        self.create_audio()
        self.makeNewShip = False
        self.shipAlive = True

    def make_blockers(self, number):
        blockerGroup = sprite.Group()
        for row in range(4):
            for column in range(9):
                blocker = Blocker(10, GREEN2, row, column)
                blocker.rect.x = 50 + (200 * number) + (column * blocker.width)
                blocker.rect.y = BLOCKERS_POSITION + (row * blocker.height)
                blockerGroup.add(blocker)
        return blockerGroup

    def create_audio(self):
        self.sounds = {}
        for sound_name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled',
                           'shipexplosion']:
            self.sounds[sound_name] = mixer.Sound(
                SOUND_PATH + '{}.wav'.format(sound_name))
            self.sounds[sound_name].set_volume(0.2)

        self.musicNotes = [mixer.Sound(SOUND_PATH + '{}.wav'.format(i)) for i
                           in range(4)]
        for sound in self.musicNotes:
            sound.set_volume(0.5)

        self.noteIndex = 0

    def play_main_music(self, currentTime):
        if currentTime - self.noteTimer > self.enemies.moveTime:
            self.note = self.musicNotes[self.noteIndex]
            if self.noteIndex < 3:
                self.noteIndex += 1
            else:
                self.noteIndex = 0

            self.note.play()
            self.noteTimer += self.enemies.moveTime

    @staticmethod
    def should_exit(evt):
        # type: (pygame.event.EventType) -> bool
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def check_input(self):
        self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    if len(self.bullets) == 0 and self.shipAlive:
                        if self.score < 1000:
                            bullet = Bullet(self.player.rect.x + 19.5,
                                            self.player.rect.y + 5, -1,
                                            15, 'laser', 'center')
                            self.bullets.add(bullet)
                            self.allSprites.add(self.bullets)
                            self.sounds['shoot'].play()
                        else:
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

    def make_enemies(self):
        enemies = EnemiesGroup(10, 5)
        for row in range(5):
            for column in range(10):
                enemy = Enemy(row, column)
                enemy.rect.x = 157 + (column * 50)
                enemy.rect.y = self.enemyPosition + (row * 45)
                enemies.add(enemy)

        self.enemies = enemies

    def make_enemies_shoot(self):
        if (time.get_ticks() - self.timer) > 700 and self.enemies:
            enemy = self.enemies.random_bottom()
            self.enemyBullets.add(
                Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 1, 5,
                       'enemylaser', 'center'))
            self.allSprites.add(self.enemyBullets)
            self.timer = time.get_ticks()

    def calculate_score(self, row):
        scores = {0: 30,
                  1: 20,
                  2: 20,
                  3: 10,
                  4: 10,
                  5: choice([50, 100, 150, 300])
                  }

        score = scores[row]
        self.score += score
        return score

    def create_main_menu(self):
        self.enemy1 = IMAGES['enemy3_1']
        self.enemy1 = transform.scale(self.enemy1, (40, 40))
        self.enemy2 = IMAGES['enemy2_2']
        self.enemy2 = transform.scale(self.enemy2, (40, 40))
        self.enemy3 = IMAGES['enemy1_2']
        self.enemy3 = transform.scale(self.enemy3, (40, 40))
        self.enemy4 = IMAGES['mystery']
        self.enemy4 = transform.scale(self.enemy4, (70, 60))
        self.screen.blit(self.enemy1, (318, 270))
        self.screen.blit(self.enemy2, (318, 320))
        self.screen.blit(self.enemy3, (318, 370))
        self.screen.blit(self.enemy4, (299, 412))

    def check_collisions(self):
        sprite.groupcollide(self.bullets, self.enemyBullets, True, True)

        for enemy in sprite.groupcollide(self.enemies, self.bullets,
                                         True, True).keys():
            self.sounds['invaderkilled'].play()
            self.calculate_score(enemy.row)
            EnemyExplosion(enemy, self.explosionsGroup)
            self.gameTimer = time.get_ticks()

        for mystery in sprite.groupcollide(self.mysteryGroup, self.bullets,
                                           True, True).keys():
            mystery.mysteryEntered.stop()
            self.sounds['mysterykilled'].play()
            score = self.calculate_score(mystery.row)
            MysteryExplosion(mystery, score, self.explosionsGroup)
            newShip = Mystery()
            self.allSprites.add(newShip)
            self.mysteryGroup.add(newShip)

        for player in sprite.groupcollide(self.playerGroup, self.enemyBullets,
                                          True, True).keys():
            if self.life3.alive():
                self.life3.kill()
            elif self.life2.alive():
                self.life2.kill()
            elif self.life1.alive():
                self.life1.kill()
            else:
                self.gameOver = True
                self.startGame = False
            self.sounds['shipexplosion'].play()
            ManDeath(player, self.explosionsGroup)
            self.makeNewShip = True
            self.shipTimer = time.get_ticks()
            self.shipAlive = False

        if self.enemies.bottom >= 540:
            sprite.groupcollide(self.enemies, self.playerGroup, True, True)
            if not self.player.alive() or self.enemies.bottom >= 600:
                self.gameOver = True
                self.startGame = False

        sprite.groupcollide(self.bullets, self.allBlockers, True, True)
        sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
        if self.enemies.bottom >= BLOCKERS_POSITION:
            sprite.groupcollide(self.enemies, self.allBlockers, False, True)

    def create_new_ship(self, createShip, currentTime):
        if createShip and (currentTime - self.shipTimer > 900):
            self.player = Man()
            self.allSprites.add(self.player)
            self.playerGroup.add(self.player)
            self.makeNewShip = False
            self.shipAlive = True

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
                        # Only create blockers on a new game, not a new round
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
                        self.scoreText2 = Text(FONT, 20, str(self.score),
                                               GREEN, 160, 5)
                        self.scoreText.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        self.nextRoundText.draw(self.screen)
                        self.livesText.draw(self.screen)
                        self.livesGroup.update()
                        self.check_input()
                    if currentTime - self.gameTimer > 3000:
                        # Move enemies closer to bottom
                        self.enemyPosition += ENEMY_MOVE_DOWN
                        self.reset(self.score)
                        self.gameTimer += 3000
                else:
                    currentTime = time.get_ticks()
                    self.play_main_music(currentTime)
                    self.screen.blit(self.background, (0, 0))
                    self.allBlockers.update(self.screen)
                    self.scoreText2 = Text(FONT, 20, str(self.score), GREEN,
                                           160, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.livesText.draw(self.screen)
                    self.check_input()
                    self.enemies.update(currentTime)
                    self.allSprites.update(self.keys, currentTime)
                    self.explosionsGroup.update(currentTime)
                    self.check_collisions()
                    self.create_new_ship(self.makeNewShip, currentTime)
                    self.make_enemies_shoot()

            elif self.gameOver:
                currentTime = time.get_ticks()
                # Reset enemy starting position
                self.enemyPosition = ENEMY_DEFAULT_POSITION
                self.create_game_over(currentTime)

            display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    game = SpaceInvaders()
    game.main()
