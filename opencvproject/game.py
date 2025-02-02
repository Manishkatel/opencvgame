import cv2
import mediapipe as mp
import pygame
import sys
import random

from Tools.demo.spreadsheet import CENTER

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 1200, 600
GAME_WIDTH = 800  # Width of the game section
CAM_WIDTH = 400  # Width of the webcam feed section
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Controlled Brick Breaker with Levels")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (200, 200, 200)
BUTTON_COLOR = (50, 150, 250)
BUTTON_HOVER_COLOR = (100, 200, 255)

# Paddle properties
paddle_width, paddle_height = 150, 20
paddle_x = GAME_WIDTH // 2 - paddle_width // 2
paddle_y = HEIGHT - 30
paddle_color = BLUE

# Ball properties
ball_radius = 10
ball_x, ball_y = GAME_WIDTH // 2, HEIGHT // 2
ball_speed_x, ball_speed_y = 4, -4
ball_color = RED

# Brick properties
brick_width = GAME_WIDTH // 10
brick_height = 30

# Levels
current_level = 1
max_levels = 5
ball_speed_increment = 0.5  # Increased ball speed increment

# Frame rate
clock = pygame.time.Clock()

# OpenCV video capture
cap = cv2.VideoCapture(0)

# Game states
is_game_running = False

# Function to create a grid of bricks
def create_bricks(rows):
    return [[1] * 10 for _ in range(rows)]

# Function to map hand coordinates to the Pygame window
def map_coordinates(x, y, cap_width, cap_height, screen_width, screen_height):
    mapped_x = int(x / cap_width * screen_width)
    mapped_y = int(y / cap_height * screen_height)
    return mapped_x, mapped_y

# Draw bricks
def draw_bricks(bricks):
    for row in range(len(bricks)):
        for col in range(len(bricks[row])):
            if bricks[row][col] == 1:
                brick_x = col * brick_width
                brick_y = row * brick_height
                pygame.draw.rect(screen, GREEN, (brick_x, brick_y, brick_width, brick_height))
                pygame.draw.rect(screen, BLACK, (brick_x, brick_y, brick_width, brick_height), 2)

# Reset ball and paddle
def reset_ball_and_paddle():
    global ball_x, ball_y, ball_speed_x, ball_speed_y, paddle_x
    ball_x, ball_y = GAME_WIDTH // 2, HEIGHT // 2
    ball_speed_x, ball_speed_y = 4, -4
    paddle_x = GAME_WIDTH // 2 - paddle_width // 2

# Draw the score
def draw_score(score):
    font = pygame.font.SysFont("Arial", 45)
    score_text = font.render(f"Score: {score}", True, BLACK)
    screen.blit(score_text, (808, 15))

# Draw the main menu with styled buttons
def draw_menu():
    screen.fill(WHITE)
    font = pygame.font.SysFont("Arial", 48)
    start_text = font.render("START GAME", True, WHITE)
    exit_text = font.render("EXIT", True, WHITE)

    start_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 50, 300, 70)
    exit_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 70)

    mouse_pos = pygame.mouse.get_pos()

    # Button hover effect
    start_color = BUTTON_HOVER_COLOR if start_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    exit_color = BUTTON_HOVER_COLOR if exit_rect.collidepoint(mouse_pos) else BUTTON_COLOR

    pygame.draw.rect(screen, start_color, start_rect, border_radius=10)
    pygame.draw.rect(screen, exit_color, exit_rect, border_radius=10)

    screen.blit(start_text, (start_rect.x + 50, start_rect.y + 10))
    screen.blit(exit_text, (exit_rect.x + 115, exit_rect.y + 10))

    pygame.display.flip()
    return start_rect, exit_rect

# Main game loop
def game_loop():
    global ball_x, ball_y, ball_speed_x, ball_speed_y, paddle_x, current_level

    score = 0  # Initialize score

    while current_level <= max_levels:
        # Create bricks for the current level
        bricks = create_bricks(current_level + 2)  # More rows of bricks for higher levels
        reset_ball_and_paddle()

        # Level loop
        while True:
            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return  # Return to the menu

            # Capture frame from webcam
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)  # Flip the frame for a mirror effect
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process the frame with Mediapipe
            result = hands.process(rgb_frame)
            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Get the tip of the index finger (landmark 8)
                    index_finger_tip = hand_landmarks.landmark[8]
                    h, w, _ = frame.shape
                    finger_x, finger_y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)

                    # Map the finger coordinates to the paddle position
                    paddle_x, _ = map_coordinates(finger_x, finger_y, w, h, GAME_WIDTH, HEIGHT)

            # Resize the webcam feed for display in the right section
            resized_frame = cv2.resize(frame, (CAM_WIDTH, HEIGHT))
            frame_surface = pygame.surfarray.make_surface(cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB))
            frame_surface = pygame.transform.rotate(frame_surface, -90)
            screen.blit(frame_surface, (GAME_WIDTH, 0))

            # Clear the game section
            pygame.draw.rect(screen, WHITE, (0, 0, GAME_WIDTH, HEIGHT))

            # Draw the paddle
            pygame.draw.rect(screen, paddle_color, (paddle_x, paddle_y, paddle_width, paddle_height))

            # Move the ball
            ball_x += ball_speed_x
            ball_y += ball_speed_y

            # Ball collision with walls
            if ball_x - ball_radius < 0 or ball_x + ball_radius > GAME_WIDTH:
                ball_speed_x *= -1
            if ball_y - ball_radius < 0:
                ball_speed_y *= -1

            # Ball collision with paddle
            if paddle_y < ball_y + ball_radius < paddle_y + paddle_height and paddle_x < ball_x < paddle_x + paddle_width:
                ball_speed_y *= -1
                score += 1  # Increment score when the ball hits the paddle

            # Ball collision with bricks
            brick_hit = False
            for row in range(len(bricks)):
                for col in range(len(bricks[row])):
                    if bricks[row][col] == 1:
                        brick_x = col * brick_width
                        brick_y = row * brick_height
                        if (brick_x < ball_x < brick_x + brick_width and
                                brick_y < ball_y - ball_radius < brick_y + brick_height):
                            bricks[row][col] = 0
                            ball_speed_y *= -1
                            brick_hit = True
                            score += 5  # Increase score for breaking a brick
                            break
                if brick_hit:
                    break

            # Draw the ball
            pygame.draw.circle(screen, ball_color, (ball_x, ball_y), ball_radius)

            # Draw the bricks
            draw_bricks(bricks)

            # Draw the score
            draw_score(score)

            # Increase ball speed based on score
            if score % 10 == 0:  # Increase speed every 10 points
                ball_speed_x += ball_speed_increment
                ball_speed_y += ball_speed_increment

            # Check if all bricks are cleared
            if all(brick == 0 for row in bricks for brick in row):
                current_level += 1
                if current_level <= max_levels:
                    ball_speed_x += ball_speed_increment
                    ball_speed_y += ball_speed_increment
                break

            # Game over condition
            if ball_y > HEIGHT:
                return  # Game over; return to menu

            # Update the display
            pygame.display.flip()

            # Cap the frame rate
            clock.tick(60)

# Main program
while True:
    start_button, exit_button = draw_menu()

    # Handle menu interactions
    while not is_game_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if start_button.collidepoint(mouse_x, mouse_y):
                    is_game_running = True
                elif exit_button.collidepoint(mouse_x, mouse_y):
                    cap.release()
                    pygame.quit()
                    sys.exit()

    # Run the game
    game_loop()

    # Reset state after the game ends
    is_game_running = False
    current_level = 1









