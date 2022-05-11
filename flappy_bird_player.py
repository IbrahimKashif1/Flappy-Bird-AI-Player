import random
import os
import pygame
import neat


pygame.font.init()

WINDOW_HEIGHT = 800
WINDOW_WIDTH = 500

BIRD_IMAGES = [pygame.transform.scale2x(pygame.image.load(os.path.join("flappy_bird_images", "bird_wings_up.png"))),
               pygame.transform.scale2x(pygame.image.load(os.path.join("flappy_bird_images", "bird_normal.png"))),
               pygame.transform.scale2x(pygame.image.load(os.path.join("flappy_bird_images", "bird_wings_down.png")))]
PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("flappy_bird_images", "pipe.png")))
BACKGROUND_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("flappy_bird_images", "background.png")))
FLOOR_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join("flappy_bird_images", "floor.png")))

STAT_FONT = pygame.font.SysFont("arial", 50)


class Bird:
    IMAGES = BIRD_IMAGES
    MAX_ROTATION = 25  # Indicated how much the bird will tilt
    ROTATION_VELOCITY = 20
    ANIMATION_TIME = 5  # Controls how fast bird flaps its wings

    def __init__(self, x_coordinate, y_coordinate):
        self.x = x_coordinate
        self.y = y_coordinate
        self.height = y_coordinate
        self.image_count = 0
        self.image = self.IMAGES[0]
        self.tilt_image = 0
        self.tick_count = 0
        self.velocity = 0

    def jump(self):
        self.tick_count = 0  # Reset tick_count
        self.velocity = -10.5  # Sets velocity to -10.5
        self.height = self.y  # Sets the height of the bird

    def move(self):
        self.tick_count = self.tick_count + 1
        displacement = (self.velocity * self.tick_count) + (1.5 * self.tick_count ** 2)  # Computation of displacement
        if displacement >= 16:
            displacement = 16  # Sets maximum displacement
        elif displacement < 0:
            displacement = displacement - 2
        self.y = self.y + displacement  # Current position of bird along y-axis
        if self.y < (self.height + 50) or displacement < 0:
            if self.tilt_image < self.MAX_ROTATION:
                self.tilt_image = self.MAX_ROTATION  # Sets the tilt to MAX_ROTATION
        else:
            if self.tilt_image > -90:
                self.tilt_image = self.tilt_image - self.ROTATION_VELOCITY

    def draw(self, win):
        self.image_count = self.image_count + 1
        if self.image_count <= self.ANIMATION_TIME:
            self.image = self.IMAGES[0]
        elif self.image_count <= (2 * self.ANIMATION_TIME):
            self.image = self.IMAGES[1]
        elif self.image_count <= (3 * self.ANIMATION_TIME):
            self.image = self.IMAGES[2]
        elif self.image_count <= (4 * self.ANIMATION_TIME):
            self.image = self.IMAGES[1]
        elif self.image_count <= (self.ANIMATION_TIME * 4 + 1):
            self.image = self.IMAGES[0]
            self.image_count = 0

        if self.tilt_image <= -80:
            self.image = self.IMAGES[1]
            self.image_count = (self.ANIMATION_TIME * 2)

        # Rotates bird according to the tilt
        rotated_image = pygame.transform.rotate(self.image, self.tilt_image)
        new_rect = rotated_image.get_rect(center=self.image.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):

        # Gets mask for bird
        return pygame.mask.from_surface(self.image)


class Pipe:
    SPACE = 200
    VELOCITY = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        # Flips the pipe image and sets the value of self.PIPE_TOP to the flipped image
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMAGE, False, True)
        self.PIPE_BOTTOM = PIPE_IMAGE
        self.gone = False
        self.set_pipe_height()

    def set_pipe_height(self):
        self.height = random.randrange(50, 450)  # Makes the height of each pipe different from the next
        self.top = self.height - self.PIPE_TOP.get_height()  # Adjusts the heights for the pipe
        self.bottom = self.height + self.SPACE

    def move_pipe(self):
        self.x = self.x - self.VELOCITY

    def draw_pipe(self, window):
        window.blit(self.PIPE_TOP, (self.x, self.top))
        window.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()  # Gets the bird mask
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)  # Gets the mask for the top pipe
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)  # Gets the mask for the bottom pipe

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        top_point = bird_mask.overlap(top_mask, top_offset)
        bottom_point = bird_mask.overlap(bottom_mask, bottom_offset)

        # Check if their is an overlap between the bird and the top or bottom pipe
        if bottom_point or top_point:
            return True
        else:
            return False


class Floor:
    VELOCITY = 5
    WIDTH = FLOOR_IMAGE.get_width()
    IMAGE = FLOOR_IMAGE

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VELOCITY
        self.x2 -= self.VELOCITY

        if self.WIDTH + self.x1 < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.WIDTH + self.x2 < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMAGE, (self.x1, self.y))
        win.blit(self.IMAGE, (self.x2, self.y))


def draw_win(window, birds, pipes, floor, score):
    window.blit(BACKGROUND_IMAGE, (0, 0))  # Sets the background image of the window
    for pipe in pipes:
        pipe.draw_pipe(window)  # Draws the pipes

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    window.blit(text, (WINDOW_WIDTH - 10 - text.get_width(), 50))
    floor.draw(window)  # Draws the floor
    for bird in birds:
        bird.draw(window)  # Draws the birds
    pygame.display.update()  # Updates the window


def main(genomes, config):
    global bird
    gen = []
    birds = []
    nets = []

    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        genome.fitness = 0
        gen.append(genome)

    score = 0
    con = True
    floor = Floor(730)
    pipes = [Pipe(700)]
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    while con:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                con = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            con = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            gen[x].fitness += 0.1
            output = nets[birds.index(bird)].activate(
                (bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        bird.move()
        remove = []
        add_pipe = False
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    gen[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    gen.pop(x)

                if not pipe.gone and pipe.x < bird.x:
                    pipe.gone = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                remove.append(pipe)

            pipe.move_pipe()

        if add_pipe:
            score += 1
            for g in gen:
                g.fitness += 5
            pipes.append(Pipe(600))

        for rem in remove:
            pipes.remove(rem)

        for x, bird in enumerate(birds):
            if bird.y + bird.image.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                gen.pop(x)

        floor.move()
        draw_win(window, birds, pipes, floor, score)


def run(config_path1):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path1)

    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config.txt")
    run(config_path)