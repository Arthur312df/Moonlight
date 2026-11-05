import math
import threading
import pygame


class MoonlightCoreUI:

  def __init__(self):
    self.is_processing = False
    self.running = True
    self.thread = threading.Thread(target=self._run_loop, daemon=True)

  def start(self):
    self.thread.start()

  def set_processing(self, state: bool):
    self.is_processing = state

  def stop(self):
    self.running = False
    try:
      pygame.quit()
    except Exception:
      pass

  def _run_loop(self):
    pygame.init()
    WIDTH, HEIGHT = 900, 900
    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT), pygame.RESIZABLE | pygame.HWSURFACE | pygame.DOUBLEBUF
    )
    pygame.display.set_caption(
        "Moonlight - Arquiteto Core (Pressione ESC para sair)"
    )
    clock = pygame.time.Clock()

    TOP_COLOR = (12, 85, 95)
    BOTTOM_COLOR = (12, 10, 35)

    def draw_vertical_gradient(surface, width, height):
      for y in range(0, height, 2):
        factor = y / height
        r = int(TOP_COLOR[0] + (BOTTOM_COLOR[0] - TOP_COLOR[0]) * factor)
        g = int(TOP_COLOR[1] + (BOTTOM_COLOR[1] - TOP_COLOR[1]) * factor)
        b = int(TOP_COLOR[2] + (BOTTOM_COLOR[2] - TOP_COLOR[2]) * factor)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y), 2)

    class Dot:

      def __init__(self, index, total_dots, width, height):
        self.index = index
        self.total_dots = total_dots
        self.phase = index * 1.2
        self.frequency = 0.15 + (index * 0.03)
        self.amplitude = 18 + (index % 2) * 10
        bx, by = self.get_base_position(width, height)
        self.x = bx
        self.y = by

      def get_base_position(self, width, height):
        center_x, center_y = width // 2, height // 2
        spacing = 45
        total_width = (self.total_dots - 1) * spacing
        start_x = center_x - (total_width / 2)
        return start_x + (self.index * spacing), center_y

      def update(self, processing, width, height):
        bx, by = self.get_base_position(width, height)
        if processing:
          self.phase += self.frequency
          offset_y = (
              math.sin(self.phase) * self.amplitude
              + math.cos(self.phase * 0.7) * 8
          )
          self.y = by + offset_y
          self.x = bx
        else:
          self.y += (by - self.y) * 0.15
          self.x += (bx - self.x) * 0.15

      def draw(self, surface):
        scale_factor = 8
        size = 30 * scale_factor
        dot_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        pygame.draw.circle(
            dot_surf, (220, 240, 255, 50), (center, center), 8 * scale_factor
        )
        pygame.draw.circle(
            dot_surf, (255, 255, 255, 255), (center, center), 4 * scale_factor
        )

        final_size = size // scale_factor
        smooth_surf = pygame.transform.smoothscale(
            dot_surf, (final_size, final_size)
        )
        surface.blit(
            smooth_surf,
            (int(self.x) - final_size // 2, int(self.y) - final_size // 2),
        )

    dots = [Dot(i, 5, WIDTH, HEIGHT) for i in range(5)]

    while self.running:
      try:
        current_width, current_height = screen.get_size()
      except pygame.error:
        break

      draw_vertical_gradient(screen, current_width, current_height)

      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          self.running = False
        elif event.type == pygame.KEYDOWN:
          if event.key == pygame.K_ESCAPE:  # Aperte ESC para fechar na hora
            self.running = False
        elif event.type == pygame.VIDEORESIZE:
          screen = pygame.display.set_mode(
              (event.w, event.h),
              pygame.RESIZABLE | pygame.HWSURFACE | pygame.DOUBLEBUF,
          )

      for dot in dots:
        dot.update(self.is_processing, current_width, current_height)
        dot.draw(screen)

      pygame.display.flip()
      clock.tick(60)

    try:
      pygame.quit()
    except Exception:
      pass