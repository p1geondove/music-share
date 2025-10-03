import pygame

from scripts.orchester import Orchestrator
from scripts.helpers import mkdirs
from scripts.const import Sizes

def main():
    pygame.mixer.init()
    pygame.font.init()

    window = pygame.display.set_mode(Sizes.window, pygame.SRCALPHA)
    clock = pygame.Clock()

    mkdirs()
    orchester = Orchestrator(window, None)

    while True:
        for event in pygame.event.get():
            if o:=orchester.handle_event(event):
                orchester = o

        orchester.draw()
        pygame.display.flip()
        pygame.display.set_caption(f"{clock.get_fps():.0f}")
        clock.tick()

if __name__ == "__main__":
    main()
