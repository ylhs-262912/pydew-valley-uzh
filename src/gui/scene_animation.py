import pygame


class SceneAnimation:
    def __init__(self, target_points):
        self.target_points = target_points 
        self.speed = 200
        self.current_index = 0  
        self.current_pos = pygame.Vector2(target_points[0])
        self.is_finished = False

    def update(self, dt):
        if self.is_finished or self.current_index >= len(self.target_points) - 1:
            self.kill()
            return

        target = pygame.Vector2(self.target_points[self.current_index])
        direction = target - self.current_pos

        if direction.length() <= self.speed * dt:
            self.current_pos = target
            self.current_index += 1
            if self.current_index >= len(self.target_points):
                self.is_finished = True
        else:
            direction = direction.normalize()
            self.current_pos += direction * self.speed * dt

    def get_current_position(self):
        return self.current_pos

    def reset(self):
        self.current_index = 0
        self.current_pos = pygame.Vector2(self.target_points[0])
        self.is_finished = False