import pygame

from scripts.orchester import Orchester
from scripts.const import Sizes

def main():
    pygame.init()
    pygame.mixer.init()

    window = pygame.display.set_mode(Sizes.window, pygame.SRCALPHA)
    clock = pygame.Clock()
    orchester = Orchester(window, None)

    while True:
        for event in pygame.event.get():
            orchester.handle_event(event)

        orchester.draw()
        pygame.display.flip()
        pygame.display.set_caption(f"{clock.get_fps():.0f}")
        clock.tick(Sizes.preview_fps)

if __name__ == "__main__":
    main()
