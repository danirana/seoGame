import pygame
import random
import time



# Initialize Pygame
pygame.init()

pygame.mixer.init()

hit_sound = pygame.mixer.Sound("sounds/hit.ogg")  # Make sure the path is correct
celebration_music = pygame.mixer.Sound("sounds/celebration.wav")

# Screen dimensions and setup
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Dodge the Falling Blocks - 3 Levels")

# Player setup
player_width, player_height = 250, 150
player_x = (screen_width - player_width) // 2
player_y = screen_height - player_height - 10 
player_speed = 10
player_color = (0, 255, 0)  # Green
player_rect = pygame.Rect(player_x, player_y, player_width, player_height)

# Load images
rock_image = pygame.image.load("images/rock.png").convert_alpha()
rock_image = pygame.transform.scale(rock_image, (80, 80))  # Adjust size as needed

player_image = pygame.image.load("images/icon.png").convert_alpha()
player_image = pygame.transform.scale(player_image, (player_width, player_height))


# Define colors
background_color = (130, 201, 230)  # Black
block_color = (255, 0, 0)  # Red for falling circles




# Frame rate control
clock = pygame.time.Clock()




# Game state variables
current_level = 1
max_levels = 3
player_score = 0
winning_scores = [10, 20, 30]  # Score needed to win each level
fall_speeds = [5, 7, 10]  # Base fall speeds for each level
spawn_delays = [120, 90, 60]  # Spawn delays for each level
max_blocks_per_level = [20, 30, 40]  # Max Blocks on screen per level



# Font for displaying text
font = pygame.font.Font(None, 36)




def reset_level():
    """Reset game variables for a new level"""
    global blocks, spawn_timer, fall_speed, spawn_delay, max_blocks
    blocks = []
    spawn_timer = 0
    fall_speed = fall_speeds[current_level - 1]
    spawn_delay = spawn_delays[current_level - 1]
    max_blocks = max_blocks_per_level[current_level - 1]
    # Add some initial circles
    for _ in range(3):
        blocks.append([random.randint(0, screen_width), random.randint(0, screen_height // 2)])




def show_level_start():
    """Display level start message"""

    # Stop any currently playing music
    pygame.mixer.music.stop()

     # Load and play music
    pygame.mixer.music.load("sounds/background.wav")
    pygame.mixer.music.set_volume(0.1)  # Lower volume for music
    pygame.mixer.music.play(-1)  # Loop indefinitely

    screen.fill(background_color)
    level_text = font.render(f"Level {current_level}", True, (255, 255, 255))
    start_text = font.render("Press SPACE to start", True, (255, 255, 255))
    screen.blit(level_text, (screen_width // 2 - 50, screen_height // 2 - 50))
    screen.blit(start_text, (screen_width // 2 - 120, screen_height // 2 + 20))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False
    return True

def run_confetti(duration=3):
    confetti_particles = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]
    
    start_time = time.time()
    while time.time() - start_time < duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        screen.fill(background_color)
        
        # Add new confetti particles
        if len(confetti_particles) < 100:
            confetti_particles.append([random.randint(0, screen_width), 0, random.choice(colors), random.randint(2, 5)])

        # Update and draw particles
        for p in confetti_particles:
            p[1] += p[3]  # move down by speed p[3]
            pygame.draw.circle(screen, p[2], (p[0], p[1]), 5)
        
        # Remove particles that go off screen
        confetti_particles = [p for p in confetti_particles if p[1] < screen_height]

        pygame.display.flip()
        clock.tick(60)

def play_celebration():
    # Stop the background music
    pygame.mixer.music.stop()
    
    # Play celebration sound
    celebration_music.play()

    # Run confetti animation (you can expand this function)
    run_confetti()



# Initialize first level
reset_level()
if not show_level_start():
    running = False




# Main game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False




        # Add a new circle when the spacebar is pressed
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                blocks.append([random.randint(0, screen_width), 0])




    # Handle player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_rect.x > 0:
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT] and player_rect.x < screen_width - player_width:
        player_rect.x += player_speed




    # Game logic
    spawn_timer += 1




    # Spawn new circles automatically
    if spawn_timer >= spawn_delay:
        blocks.append([random.randint(0, screen_width), 0])
        spawn_timer = 0




    # Remove circles that go off screen
    blocks = [block for block in blocks if block[1] < screen_height]




    # Limit the number of circles
    if len(blocks) > max_blocks:
        blocks.pop(0)




    # Increase speed based on score (within current level)
    current_speed_increase = min(player_score * 0.5, 5)  # Cap at +5 speed
    current_fall_speed = fall_speed + current_speed_increase




    # Update circle positions
    for block in blocks:
        block[1] += current_fall_speed




    # Check for collisions
    for block in blocks[:]:
        block_rect = pygame.Rect(block[0] - 15, block[1] - 15, 30, 30)




        if block[1] >= screen_height:
            if not player_rect.colliderect(block_rect):
                player_score += 1
            blocks.remove(block)




        if player_rect.colliderect(block_rect):
            hit_sound.play()
            blocks.remove(block)
            player_color = (255, 0, 0)
            player_score -= 1




        # Check if level is complete
        if player_score >= winning_scores[current_level - 1]:
                if current_level < max_levels:
                    current_level += 1
                    player_score = 0
                    if not show_level_start():
                        running = False
                    reset_level()
                else:
                    play_celebration()
                    # Game won
                    win_text = font.render("You Won All Levels!", True, (0, 255, 0))
                    screen.fill(background_color)
                    screen.blit(win_text, (screen_width // 2 - 150, screen_height // 2 - 20))
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    running = False
                    break




    # Drawing
    screen.fill(background_color)
   
    # Draw blocks
    for block in blocks:
        random_number = random.uniform(100,200)
        random_number1 = random.uniform(20,30)




        x = random_number
        y = random_number1
        screen.blit(rock_image, (block[0], block[1]))
   
    # Draw player
    screen.blit(player_image, player_rect)
   
    # Draw UI
    score_text = font.render(f"Score: {player_score}", True, (255, 255, 255))
    level_text = font.render(f"Level: {current_level}/{max_levels}", True, (255, 255, 255))
    target_text = font.render(f"Target: {winning_scores[current_level - 1]}", True, (255, 255, 255))
   
    screen.blit(score_text, (10, 10))
    screen.blit(level_text, (10, 50))
    screen.blit(target_text, (10, 90))




    # Reset player color
    # player_color = (0, 255, 0)




    pygame.display.flip()
    clock.tick(60)




pygame.quit()


