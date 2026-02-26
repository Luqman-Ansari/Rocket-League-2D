# physics.py
import math
from src.settings import *


class Physics:
    """Physics engine for collision detection and resolution."""
    
    @staticmethod
    def collide_circle(a_x, a_y, a_r, b_x, b_y, b_r):
        """
        Detect collision between two circles.
        
        Returns:
            tuple: (collided, nx, ny, overlap) where:
                - collided: bool indicating if collision occurred
                - nx, ny: normalized collision normal vector
                - overlap: penetration depth
        """
        dx = b_x - a_x
        dy = b_y - a_y
        dist = math.hypot(dx, dy)
        
        if dist == 0 or dist >= (a_r + b_r):
            return False, 0, 0, 0
        
        overlap = (a_r + b_r) - dist
        nx = dx / dist
        ny = dy / dist
        
        return True, nx, ny, overlap
    
    @staticmethod
    def resolve_car_ball(car, ball):
        """
        Resolve collision between a car and the ball.
        
        Applies elastic collision with momentum transfer and spin.
        
        Args:
            car: Car instance
            ball: Ball instance
        """
        collided, nx, ny, overlap = Physics.collide_circle(
            car.x, car.y, car.radius,
            ball.x, ball.y, ball.radius
        )
        
        if not collided:
            return
        
        # Positional correction - move ball out of car
        ball.x += nx * overlap
        ball.y += ny * overlap
        
        # Relative velocity
        rx = ball.vx - car.vx
        ry = ball.vy - car.vy
        
        # Velocity along collision normal
        impact_speed = rx * nx + ry * ny
        
        if impact_speed < 0:
            # Apply impulse with restitution
            impulse = -impact_speed * 1.3
            ball.vx += nx * impulse
            ball.vy += ny * impulse
            
            # Car receives some kickback
            car.vx -= nx * impulse * 0.3
            car.vy -= ny * impulse * 0.3
            
            # Add spin to ball (tangent impulse)
            tx = -ny  # tangent vector
            ty = nx
            tangent_speed = rx * tx + ry * ty
            ball.ang_vel += tangent_speed * 2.0
    
    @staticmethod
    def resolve_car_car(c1, c2):
        """
        Resolve collision between two cars.
        
        Uses elastic collision with position correction.
        
        Args:
            c1: First Car instance
            c2: Second Car instance
        """
        collided, nx, ny, overlap = Physics.collide_circle(
            c1.x, c1.y, c1.radius,
            c2.x, c2.y, c2.radius
        )
        
        if not collided:
            return
        
        # Position correction - push cars apart
        sep = overlap / 2 + 0.1
        c1.x -= nx * sep
        c1.y -= ny * sep
        c2.x += nx * sep
        c2.y += ny * sep
        
        # Velocity exchange along collision normal
        v1n = c1.vx * nx + c1.vy * ny
        v2n = c2.vx * nx + c2.vy * ny
        
        # Apply momentum transfer
        c1.vx += (v2n - v1n) * nx * 0.6
        c1.vy += (v2n - v1n) * ny * 0.6
        c2.vx += (v1n - v2n) * nx * 0.6
        c2.vy += (v1n - v2n) * ny * 0.6


# Legacy functions for backwards compatibility
def collide_circle(a_x, a_y, a_r, b_x, b_y, b_r):
    """Legacy function - use Physics.collide_circle instead."""
    return Physics.collide_circle(a_x, a_y, a_r, b_x, b_y, b_r)


def resolve_car_ball(car, ball):
    """Legacy function - use Physics.resolve_car_ball instead."""
    Physics.resolve_car_ball(car, ball)


def resolve_car_car(c1, c2):
    """Legacy function - use Physics.resolve_car_car instead."""
    Physics.resolve_car_car(c1, c2)