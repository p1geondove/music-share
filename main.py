import pygame

from scripts.orchester import Orchester
from scripts.helpers import tmp_cleanup
from scripts.const import Sizes

def main():
    pygame.mixer.init()
    pygame.font.init()

    window = pygame.display.set_mode(Sizes.window, pygame.SRCALPHA)
    clock = pygame.Clock()

    orchester = Orchester(window, None)
    orchester.draw_info("removing old images")
    tmp_cleanup()

    while True:
        for event in pygame.event.get():
            orchester.handle_event(event)

        orchester.draw()
        pygame.display.flip()
        pygame.display.set_caption(f"{clock.get_fps():.0f}")
        clock.tick()

if __name__ == "__main__":
    main()
