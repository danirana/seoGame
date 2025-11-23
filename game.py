import pygame
import random
import time
import math
import json
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Try to load sounds, handle if missing
try:
    hit_sound = pygame.mixer.Sound("sounds/hit.ogg")
except:
    hit_sound = None

try:
    celebration_music = pygame.mixer.Sound("sounds/celebration.wav")
except:
    celebration_music = None

# Screen dimensions and setup
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Dodge the Falling Blocks - Ultimate Edition")

# Player setup
player_width, player_height = 250, 150
player_x = (screen_width - player_width) // 2
player_y = screen_height - player_height - 10
base_player_speed = 10
player_speed = base_player_speed
player_rect = pygame.Rect(player_x, player_y, player_width, player_height)

# Load images
try:
    rock_image = pygame.image.load("images/rock.png").convert_alpha()
    rock_image = pygame.transform.scale(rock_image, (80, 80))
except:
    rock_image = None

try:
    player_image = pygame.image.load("images/icon.png").convert_alpha()
    player_image = pygame.transform.scale(player_image, (player_width, player_height))
except:
    player_image = None

# Define colors
background_color = (10, 15, 25)  # Very dark blue
block_colors = [
    (255, 100, 100),  # Red
    (255, 200, 100),  # Orange
    (255, 255, 100),  # Yellow
    (100, 255, 100),  # Green
    (100, 200, 255),  # Blue
]

# Frame rate control
clock = pygame.time.Clock()

# Game state
game_state = "menu"  # menu, playing, boss, game_over, shop
current_level = 1
max_levels = 5
player_score = 0
player_lives = 3
max_lives = 3
combo = 0
max_combo = 0
coins = 0
total_score = 0
winning_scores = [15, 25, 40, 60, 80]
fall_speeds = [4, 6, 8, 10, 12]
spawn_delays = [100, 80, 60, 45, 35]
max_blocks_per_level = [15, 25, 35, 45, 55]

# High score system
high_score_file = "highscore.json"

def load_high_score():
    """Load high score from file"""
    try:
        if os.path.exists(high_score_file):
            with open(high_score_file, 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0), data.get('max_combo', 0)
    except:
        pass
    return 0, 0

def save_high_score(score, combo):
    """Save high score to file"""
    try:
        data = {'high_score': score, 'max_combo': combo}
        with open(high_score_file, 'w') as f:
            json.dump(data, f)
    except:
        pass

high_score, high_combo = load_high_score()

# Power-up system
power_ups = []
power_up_types = ['shield', 'speed', 'slow_motion', 'multiplier', 'ultimate']
active_power_ups = {}
power_up_spawn_timer = 0
power_up_spawn_delay = 600

# Ultimate ability system
ultimate_charge = 0
max_ultimate_charge = 100
ultimate_active = False
ultimate_duration = 0
ultimate_cooldown = 0

# Particle system
particles = []

# Player trail system
player_trail = []

# Parallax background stars
stars = []
for _ in range(100):
    stars.append({
        'x': random.randint(0, screen_width),
        'y': random.randint(0, screen_height),
        'speed': random.uniform(0.5, 2),
        'size': random.randint(1, 3),
        'layer': random.randint(1, 3)
    })

# Screen shake
screen_shake = 0
shake_intensity = 0

# Obstacle types
obstacle_types = ['normal', 'fast', 'slow', 'bouncy', 'splitter', 'homing']

# Boss system
boss_active = False
boss_health = 0
boss_max_health = 0
boss_x = screen_width // 2
boss_y = -100
boss_pattern = 0
boss_timer = 0

# Upgrades
upgrades = {
    'speed': 0,
    'lives': 0,
    'ultimate_charge_rate': 0,
    'coin_multiplier': 0
}

# Achievements
achievements = {
    'first_combo_10': False,
    'first_combo_50': False,
    'first_boss_defeated': False,
    'perfect_level': False,
    'high_score_100': False
}

# Fonts
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 24)
tiny_font = pygame.font.Font(None, 18)

# Time tracking
game_time = 0
invulnerability_time = 0
invulnerability_duration = 60

def create_particles(x, y, color, count=10, speed_range=(2, 5)):
    """Create particle explosion effect"""
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(speed_range[0], speed_range[1])
        particles.append({
            'x': x,
            'y': y,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed,
            'color': color,
            'life': 30,
            'size': random.randint(2, 5)
        })

def update_particles():
    """Update and remove dead particles"""
    global particles
    for p in particles[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += 0.2
        p['life'] -= 1
        if p['life'] <= 0:
            particles.remove(p)

def draw_particles():
    """Draw all particles"""
    for p in particles:
        alpha = min(255, p['life'] * 8)
        # Get base color (first 3 values)
        base_color = p['color'][:3] if len(p['color']) >= 3 else p['color']
        # Create surface with alpha for fading effect
        if alpha < 255:
            particle_surface = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, (*base_color, alpha), (p['size'], p['size']), p['size'])
            screen.blit(particle_surface, (int(p['x']) - p['size'], int(p['y']) - p['size']))
        else:
            pygame.draw.circle(screen, base_color, (int(p['x']), int(p['y'])), p['size'])

def update_stars():
    """Update parallax stars"""
    global stars
    for star in stars:
        star['y'] += star['speed'] * (0.3 if 'slow_motion' in active_power_ups else 1.0)
        if star['y'] > screen_height:
            star['y'] = 0
            star['x'] = random.randint(0, screen_width)

def draw_stars():
    """Draw parallax stars"""
    for star in stars:
        brightness = min(255, 150 + star['layer'] * 50)
        color = (brightness, brightness, brightness)
        pygame.draw.circle(screen, color, (int(star['x']), int(star['y'])), star['size'])

def update_player_trail():
    """Update player trail effect"""
    global player_trail
    # Add current position to trail
    player_trail.append({
        'x': player_rect.centerx,
        'y': player_rect.centery,
        'life': 15
    })
    # Update and remove old trail
    for trail in player_trail[:]:
        trail['life'] -= 1
        if trail['life'] <= 0:
            player_trail.remove(trail)

def draw_player_trail():
    """Draw player trail"""
    for i, trail in enumerate(player_trail):
        alpha = int(255 * (trail['life'] / 15))
        size = int(20 * (trail['life'] / 15))
        if player_image:
            # Draw faded player image
            trail_surface = pygame.Surface((player_width, player_height), pygame.SRCALPHA)
            trail_surface.set_alpha(alpha // 3)
            trail_surface.blit(player_image, (0, 0))
            screen.blit(trail_surface, (trail['x'] - player_width // 2, trail['y'] - player_height // 2))
        else:
            # Use a surface with alpha for the circle
            trail_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (0, 255, 0, alpha), (size, size), size)
            screen.blit(trail_surface, (int(trail['x']) - size, int(trail['y']) - size))

def create_power_up():
    """Create a random power-up"""
    power_type = random.choice(power_up_types)
    power_ups.append({
        'x': random.randint(50, screen_width - 50),
        'y': -30,
        'type': power_type,
        'size': 30,
        'rotation': 0,
        'pulse': 0
    })

def update_power_ups():
    """Update power-up positions and check collisions"""
    global power_ups, active_power_ups, player_speed, player_lives, combo, ultimate_charge
    for power in power_ups[:]:
        power['y'] += 3
        power['rotation'] += 2
        power['pulse'] += 0.1
        
        power_rect = pygame.Rect(power['x'] - power['size']//2, power['y'] - power['size']//2,
                                 power['size'], power['size'])
        if player_rect.colliderect(power_rect):
            if power['type'] == 'ultimate':
                ultimate_charge = min(max_ultimate_charge, ultimate_charge + 25)
            else:
                activate_power_up(power['type'])
            create_particles(power['x'], power['y'], (255, 255, 0), 20)
            power_ups.remove(power)
        
        if power['y'] > screen_height + 50:
            power_ups.remove(power)

def activate_power_up(power_type):
    """Activate a power-up effect"""
    global active_power_ups, player_speed, player_lives
    duration = 300
    
    if power_type == 'shield':
        active_power_ups['shield'] = duration
        if player_lives < max_lives:
            player_lives = min(max_lives, player_lives + 1)
    elif power_type == 'speed':
        active_power_ups['speed'] = duration
        player_speed = (base_player_speed + upgrades['speed']) * 1.8
    elif power_type == 'slow_motion':
        active_power_ups['slow_motion'] = duration
    elif power_type == 'multiplier':
        active_power_ups['multiplier'] = duration

def update_active_power_ups():
    """Update active power-up timers"""
    global active_power_ups, player_speed
    for power_type in list(active_power_ups.keys()):
        active_power_ups[power_type] -= 1
        if active_power_ups[power_type] <= 0:
            del active_power_ups[power_type]
            if power_type == 'speed':
                player_speed = base_player_speed + upgrades['speed']

def draw_power_up(power):
    """Draw a power-up with animation"""
    size = power['size'] + int(math.sin(power['pulse']) * 5)
    color_map = {
        'shield': (100, 200, 255),
        'speed': (255, 200, 100),
        'slow_motion': (200, 100, 255),
        'multiplier': (255, 255, 100),
        'ultimate': (255, 100, 255)
    }
    color = color_map.get(power['type'], (255, 255, 255))
    
    points = []
    for i in range(6):
        angle = (power['rotation'] + i * 60) * math.pi / 180
        px = power['x'] + math.cos(angle) * size // 2
        py = power['y'] + math.sin(angle) * size // 2
        points.append((px, py))
    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, (255, 255, 255), points, 2)

def activate_ultimate():
    """Activate ultimate ability"""
    global ultimate_active, ultimate_duration, ultimate_charge, ultimate_cooldown
    if ultimate_charge >= max_ultimate_charge and ultimate_cooldown <= 0:
        ultimate_active = True
        ultimate_duration = 180  # 3 seconds
        ultimate_charge = 0
        ultimate_cooldown = 300  # 5 second cooldown
        # Clear all obstacles on screen
        for block in blocks[:]:
            create_particles(block['x'] + block['size']//2, block['y'] + block['size']//2,
                           (255, 200, 0), 30)
            blocks.remove(block)
        add_screen_shake(15)

def create_obstacle():
    """Create a random obstacle with type"""
    obstacle_type = random.choice(obstacle_types)
    return {
        'x': random.randint(0, screen_width - 80),
        'y': -80,
        'type': obstacle_type,
        'speed': fall_speeds[current_level - 1] + (2 if obstacle_type == 'fast' else -1 if obstacle_type == 'slow' else 0),
        'rotation': 0,
        'bounce': 0 if obstacle_type != 'bouncy' else random.choice([-1, 1]),
        'size': 60 if obstacle_type == 'slow' else 80 if obstacle_type == 'fast' else 70,
        'homing_target': None if obstacle_type != 'homing' else (player_rect.centerx, player_rect.centery)
    }

def update_obstacle_homing(block):
    """Update homing obstacle to track player"""
    if block['type'] == 'homing' and block['y'] > 0:
        target_x, target_y = player_rect.centerx, player_rect.centery
        dx = target_x - block['x']
        dy = target_y - block['y']
        distance = math.sqrt(dx*dx + dy*dy)
        if distance > 0:
            block['x'] += (dx / distance) * 2
            block['x'] = max(0, min(screen_width - block['size'], block['x']))

def create_boss():
    """Create a boss for the level"""
    global boss_active, boss_health, boss_max_health, boss_x, boss_y, boss_pattern, boss_timer
    boss_active = True
    boss_max_health = 50 + current_level * 20
    boss_health = boss_max_health
    boss_x = screen_width // 2
    boss_y = 50
    boss_pattern = 0
    boss_timer = 0

def update_boss():
    """Update boss behavior and attacks"""
    global boss_health, boss_x, boss_y, boss_pattern, boss_timer, blocks, boss_active
    
    if not boss_active:
        return
    
    boss_timer += 1
    
    # Boss movement pattern
    boss_x = screen_width // 2 + math.sin(boss_timer * 0.05) * 200
    
    # Boss attack patterns
    if boss_timer % 60 == 0:  # Every second
        # Spawn obstacles in patterns
        if boss_pattern == 0:  # Spread pattern
            for i in range(5):
                blocks.append({
                    'x': boss_x + (i - 2) * 100,
                    'y': boss_y + 50,
                    'type': 'fast',
                    'speed': 8,
                    'rotation': 0,
                    'bounce': 0,
                    'size': 60
                })
        elif boss_pattern == 1:  # Circle pattern
            for i in range(8):
                angle = (i / 8) * 2 * math.pi
                blocks.append({
                    'x': boss_x + math.cos(angle) * 100,
                    'y': boss_y + math.sin(angle) * 100,
                    'type': 'normal',
                    'speed': 6,
                    'rotation': 0,
                    'bounce': 0,
                    'size': 50
                })
        boss_pattern = (boss_pattern + 1) % 2

def draw_boss():
    """Draw the boss"""
    if not boss_active:
        return
    
    # Boss body
    boss_size = 120
    boss_rect = pygame.Rect(boss_x - boss_size//2, boss_y - boss_size//2, boss_size, boss_size)
    
    # Pulsing effect
    pulse = int(math.sin(game_time * 0.3) * 10)
    boss_rect.inflate_ip(pulse, pulse)
    
    # Draw boss with glow
    pygame.draw.circle(screen, (255, 50, 50), (int(boss_x), int(boss_y)), boss_size//2 + pulse)
    pygame.draw.circle(screen, (255, 150, 150), (int(boss_x), int(boss_y)), boss_size//2)
    pygame.draw.circle(screen, (255, 200, 200), (int(boss_x), int(boss_y)), boss_size//3)
    
    # Health bar
    bar_width = 300
    bar_height = 20
    bar_x = screen_width // 2 - bar_width // 2
    bar_y = 10
    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
    health_width = int(bar_width * (boss_health / boss_max_health))
    pygame.draw.rect(screen, (255, 50, 50), (bar_x, bar_y, health_width, bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
    
    boss_text = font.render("BOSS", True, (255, 255, 255))
    screen.blit(boss_text, (screen_width // 2 - boss_text.get_width() // 2, bar_y + 25))

def reset_level():
    """Reset game variables for a new level"""
    global blocks, spawn_timer, fall_speed, spawn_delay, max_blocks, power_ups, active_power_ups
    global boss_active, boss_health, ultimate_charge, ultimate_active, ultimate_duration
    blocks = []
    power_ups = []
    active_power_ups = {}
    spawn_timer = 0
    power_up_spawn_timer = 0
    fall_speed = fall_speeds[current_level - 1]
    spawn_delay = spawn_delays[current_level - 1]
    max_blocks = max_blocks_per_level[current_level - 1]
    boss_active = False
    ultimate_charge = 0
    ultimate_active = False
    ultimate_duration = 0
    for _ in range(3):
        blocks.append(create_obstacle())

def show_menu():
    """Display main menu"""
    global game_state, current_level, player_score, player_lives, combo, max_combo, coins, total_score
    
    menu_selected = 0
    menu_options = ["Start Game", "High Scores", "Upgrades", "Quit"]
    
    while game_state == "menu":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    menu_selected = (menu_selected - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    menu_selected = (menu_selected + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if menu_selected == 0:  # Start Game
                        current_level = 1
                        player_score = 0
                        player_lives = max_lives + upgrades['lives']
                        combo = 0
                        max_combo = 0
                        total_score = 0
                        reset_level()
                        game_state = "playing"
                        return True
                    elif menu_selected == 1:  # High Scores
                        show_high_scores()
                    elif menu_selected == 2:  # Upgrades
                        show_upgrade_shop()
                    elif menu_selected == 3:  # Quit
                        return False
        
        # Draw menu
        screen.fill(background_color)
        draw_stars()
        
        title = big_font.render("DODGE THE BLOCKS", True, (255, 255, 255))
        screen.blit(title, (screen_width // 2 - title.get_width() // 2, 100))
        
        subtitle = font.render("Ultimate Edition", True, (200, 200, 255))
        screen.blit(subtitle, (screen_width // 2 - subtitle.get_width() // 2, 180))
        
        for i, option in enumerate(menu_options):
            color = (255, 255, 100) if i == menu_selected else (200, 200, 200)
            option_text = font.render(option, True, color)
            screen.blit(option_text, (screen_width // 2 - option_text.get_width() // 2, 250 + i * 60))
        
        hint = small_font.render("Use UP/DOWN arrows and ENTER to select", True, (150, 150, 150))
        screen.blit(hint, (screen_width // 2 - hint.get_width() // 2, screen_height - 50))
        
        pygame.display.flip()
        clock.tick(60)
    
    return True

def show_high_scores():
    """Show high scores screen"""
    global game_state
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    waiting = False
        
        screen.fill(background_color)
        draw_stars()
        
        title = big_font.render("HIGH SCORES", True, (255, 255, 255))
        screen.blit(title, (screen_width // 2 - title.get_width() // 2, 100))
        
        score_text = font.render(f"Best Score: {high_score}", True, (255, 255, 100))
        screen.blit(score_text, (screen_width // 2 - score_text.get_width() // 2, 200))
        
        combo_text = font.render(f"Best Combo: {high_combo}x", True, (255, 255, 100))
        screen.blit(combo_text, (screen_width // 2 - combo_text.get_width() // 2, 250))
        
        hint = small_font.render("Press ESC or ENTER to return", True, (150, 150, 150))
        screen.blit(hint, (screen_width // 2 - hint.get_width() // 2, screen_height - 50))
        
        pygame.display.flip()
        clock.tick(60)
    
    return True

def show_upgrade_shop():
    """Show upgrade shop"""
    global game_state, coins, upgrades
    
    shop_selected = 0
    shop_options = [
        ("Speed Boost", upgrades['speed'], 50, 'speed'),
        ("Extra Life", upgrades['lives'], 100, 'lives'),
        ("Ultimate Charge Rate", upgrades['ultimate_charge_rate'], 75, 'ultimate_charge_rate'),
        ("Coin Multiplier", upgrades['coin_multiplier'], 150, 'coin_multiplier')
    ]
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    waiting = False
                elif event.key == pygame.K_UP:
                    shop_selected = (shop_selected - 1) % len(shop_options)
                elif event.key == pygame.K_DOWN:
                    shop_selected = (shop_selected + 1) % len(shop_options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    name, level, cost, key = shop_options[shop_selected]
                    if coins >= cost:
                        coins -= cost
                        upgrades[key] += 1
        
        screen.fill(background_color)
        draw_stars()
        
        title = big_font.render("UPGRADE SHOP", True, (255, 255, 255))
        screen.blit(title, (screen_width // 2 - title.get_width() // 2, 50))
        
        coins_text = font.render(f"Coins: {coins}", True, (255, 255, 100))
        screen.blit(coins_text, (screen_width // 2 - coins_text.get_width() // 2, 120))
        
        for i, (name, level, cost, key) in enumerate(shop_options):
            color = (255, 255, 100) if i == shop_selected else (200, 200, 200)
            option_text = font.render(f"{name} (Lv {level}) - {cost} coins", True, color)
            screen.blit(option_text, (screen_width // 2 - option_text.get_width() // 2, 180 + i * 60))
        
        hint = small_font.render("Press ESC to return, ENTER to buy", True, (150, 150, 150))
        screen.blit(hint, (screen_width // 2 - hint.get_width() // 2, screen_height - 50))
        
        pygame.display.flip()
        clock.tick(60)
    
    return True

def show_level_start():
    """Display level start message"""
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load("sounds/background.wav")
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1)
    except:
        pass

    screen.fill(background_color)
    draw_stars()
    level_text = big_font.render(f"Level {current_level}", True, (255, 255, 255))
    start_text = font.render("Press SPACE to start", True, (200, 200, 255))
    target_text = small_font.render(f"Target Score: {winning_scores[current_level - 1]}", True, (150, 150, 200))
    
    screen.blit(level_text, (screen_width // 2 - level_text.get_width() // 2, screen_height // 2 - 80))
    screen.blit(start_text, (screen_width // 2 - start_text.get_width() // 2, screen_height // 2 + 20))
    screen.blit(target_text, (screen_width // 2 - target_text.get_width() // 2, screen_height // 2 + 70))
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
    """Enhanced confetti celebration"""
    confetti_particles = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    
    start_time = time.time()
    while time.time() - start_time < duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        screen.fill(background_color)
        draw_stars()
        
        if len(confetti_particles) < 150:
            for _ in range(5):
                confetti_particles.append({
                    'x': random.randint(0, screen_width),
                    'y': -10,
                    'color': random.choice(colors),
                    'speed': random.uniform(2, 6),
                    'rotation': random.uniform(0, 360),
                    'rotation_speed': random.uniform(-5, 5),
                    'size': random.randint(3, 8)
                })

        for p in confetti_particles[:]:
            p['y'] += p['speed']
            p['x'] += math.sin(p['rotation'] * math.pi / 180) * 2
            p['rotation'] += p['rotation_speed']
            pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), p['size'])
            
            if p['y'] > screen_height:
                confetti_particles.remove(p)

        pygame.display.flip()
        clock.tick(60)

def play_celebration():
    """Play celebration sequence"""
    try:
        pygame.mixer.music.stop()
        if celebration_music:
            celebration_music.play()
    except:
        pass
    run_confetti()

def add_screen_shake(intensity=5):
    """Add screen shake effect"""
    global screen_shake, shake_intensity
    screen_shake = 10
    shake_intensity = intensity

def check_achievements():
    """Check and unlock achievements"""
    global achievements, high_score, high_combo, coins, combo, boss_active, boss_health, player_score
    
    if combo >= 10 and not achievements['first_combo_10']:
        achievements['first_combo_10'] = True
        coins += 10
    
    if combo >= 50 and not achievements['first_combo_50']:
        achievements['first_combo_50'] = True
        coins += 50
    
    if boss_active and boss_health <= 0 and not achievements['first_boss_defeated']:
        achievements['first_boss_defeated'] = True
        coins += 100
    
    if player_score >= 100 and not achievements['high_score_100']:
        achievements['high_score_100'] = True
        coins += 25

# Initialize
reset_level()
if not show_menu():
    running = False
else:
    running = True

# Main game loop
while running:
    dt = clock.tick(60) / 16.67
    game_time += 1
    
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and game_state == "playing":
                activate_ultimate()
            elif event.key == pygame.K_ESCAPE:
                game_state = "menu"
                show_menu()

    if game_state == "menu":
        if not show_menu():
            running = False
        continue
    
    if game_state != "playing":
        continue

    # Handle player movement
    keys = pygame.key.get_pressed()
    move_speed = (player_speed + upgrades['speed']) * (0.5 if 'slow_motion' in active_power_ups else 1.0)
    
    if keys[pygame.K_LEFT] and player_rect.x > 0:
        player_rect.x -= move_speed
    if keys[pygame.K_RIGHT] and player_rect.x < screen_width - player_width:
        player_rect.x += move_speed

    # Update systems
    if invulnerability_time > 0:
        invulnerability_time -= 1
    
    if ultimate_active:
        ultimate_duration -= 1
        if ultimate_duration <= 0:
            ultimate_active = False
    
    if ultimate_cooldown > 0:
        ultimate_cooldown -= 1
    
    # Charge ultimate
    if not ultimate_active and ultimate_charge < max_ultimate_charge:
        charge_rate = 0.1 + upgrades['ultimate_charge_rate'] * 0.05
        ultimate_charge = min(max_ultimate_charge, ultimate_charge + charge_rate)

    # Update background
    update_stars()
    update_player_trail()

    # Game logic
    spawn_timer += 1
    power_up_spawn_timer += 1

    # Boss logic
    if boss_active:
        update_boss()
    elif player_score >= winning_scores[current_level - 1] * 0.8 and not boss_active:
        create_boss()

    # Spawn obstacles (unless boss is active)
    if not boss_active and spawn_timer >= spawn_delay:
        blocks.append(create_obstacle())
        spawn_timer = 0

    # Spawn power-ups
    if power_up_spawn_timer >= power_up_spawn_delay:
        if random.random() < 0.3:
            create_power_up()
        power_up_spawn_timer = 0

    # Update power-ups
    update_power_ups()
    update_active_power_ups()

    # Remove obstacles off screen
    blocks = [block for block in blocks if block['y'] < screen_height + 100]

    if len(blocks) > max_blocks:
        blocks.pop(0)

    # Calculate fall speed
    speed_multiplier = 0.5 if 'slow_motion' in active_power_ups else 1.0
    if ultimate_active:
        speed_multiplier *= 0.3  # Ultimate slows everything
    current_fall_speed_multiplier = speed_multiplier * (1 + min(player_score * 0.02, 0.5))

    # Update obstacle positions
    for block in blocks:
        block['y'] += block['speed'] * current_fall_speed_multiplier
        block['rotation'] += 2
        update_obstacle_homing(block)
        
        if block['type'] == 'bouncy':
            block['x'] += block['bounce'] * 2
            if block['x'] <= 0 or block['x'] >= screen_width - block['size']:
                block['bounce'] *= -1

    # Update particles
    update_particles()

    # Check collisions
    for block in blocks[:]:
        block_rect = pygame.Rect(block['x'], block['y'], block['size'], block['size'])

        if block['y'] >= screen_height:
            if not player_rect.colliderect(block_rect):
                score_gain = 1
                if 'multiplier' in active_power_ups:
                    score_gain = 2
                score_gain += upgrades['coin_multiplier']
                player_score += score_gain
                coins += score_gain
                combo += 1
                max_combo = max(max_combo, combo)
                check_achievements()
                create_particles(block['x'] + block['size']//2, block['y'] + block['size']//2,
                                (100, 255, 100), 5)
            blocks.remove(block)

        if player_rect.colliderect(block_rect) and invulnerability_time <= 0 and not ultimate_active:
            if 'shield' in active_power_ups:
                del active_power_ups['shield']
                create_particles(block['x'] + block['size']//2, block['y'] + block['size']//2,
                                (100, 200, 255), 15)
            else:
                if hit_sound:
                    hit_sound.play()
                player_lives -= 1
                combo = 0
                invulnerability_time = invulnerability_duration
                add_screen_shake(8)
                create_particles(block['x'] + block['size']//2, block['y'] + block['size']//2,
                                (255, 100, 100), 20)
                
                if player_lives <= 0:
                    # Game over
                    total_score = player_score
                    if total_score > high_score:
                        high_score = total_score
                        save_high_score(high_score, max_combo)
                    if max_combo > high_combo:
                        high_combo = max_combo
                        save_high_score(high_score, high_combo)
                    
                    screen.fill(background_color)
                    draw_stars()
                    game_over_text = big_font.render("Game Over!", True, (255, 100, 100))
                    score_text = font.render(f"Final Score: {total_score}", True, (255, 255, 255))
                    combo_text = font.render(f"Max Combo: {max_combo}x", True, (255, 255, 255))
                    coins_text = font.render(f"Coins Earned: {coins}", True, (255, 255, 100))
                    screen.blit(game_over_text, (screen_width // 2 - game_over_text.get_width() // 2, screen_height // 2 - 150))
                    screen.blit(score_text, (screen_width // 2 - score_text.get_width() // 2, screen_height // 2 - 50))
                    screen.blit(combo_text, (screen_width // 2 - combo_text.get_width() // 2, screen_height // 2))
                    screen.blit(coins_text, (screen_width // 2 - coins_text.get_width() // 2, screen_height // 2 + 50))
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    game_state = "menu"
                    continue
            
            blocks.remove(block)

    # Boss collision and damage
    if boss_active:
        boss_rect = pygame.Rect(boss_x - 60, boss_y - 60, 120, 120)
        if player_rect.colliderect(boss_rect) and invulnerability_time <= 0:
            if 'shield' not in active_power_ups:
                player_lives -= 1
                invulnerability_time = invulnerability_duration
                add_screen_shake(10)
        
        # Boss takes damage over time (survive long enough to win)
        if game_time % 30 == 0:  # Every 0.5 seconds
            boss_health -= 1
        
        # Boss takes extra damage from ultimate
        if ultimate_active:
            boss_health -= 2
        
        # Check if boss is defeated
        if boss_health <= 0:
            boss_active = False
            coins += 50 + current_level * 10
            player_score += 20  # Bonus for defeating boss
            create_particles(boss_x, boss_y, (255, 200, 0), 100)
            add_screen_shake(20)
            check_achievements()

    # Check level completion
    if player_score >= winning_scores[current_level - 1] and not boss_active:
        if current_level < max_levels:
            current_level += 1
            player_score = 0
            player_lives = max_lives + upgrades['lives']
            combo = 0
            coins += 20
            if not show_level_start():
                game_state = "menu"
            reset_level()
        else:
            play_celebration()
            total_score = player_score
            if total_score > high_score:
                high_score = total_score
                save_high_score(high_score, max_combo)
            screen.fill(background_color)
            draw_stars()
            win_text = big_font.render("You Won All Levels!", True, (100, 255, 100))
            score_text = font.render(f"Final Score: {total_score}", True, (255, 255, 255))
            combo_text = font.render(f"Max Combo: {max_combo}x", True, (255, 255, 255))
            screen.blit(win_text, (screen_width // 2 - win_text.get_width() // 2, screen_height // 2 - 100))
            screen.blit(score_text, (screen_width // 2 - score_text.get_width() // 2, screen_height // 2))
            screen.blit(combo_text, (screen_width // 2 - combo_text.get_width() // 2, screen_height // 2 + 50))
            pygame.display.flip()
            pygame.time.wait(3000)
            game_state = "menu"

    # Screen shake
    shake_x = 0
    shake_y = 0
    if screen_shake > 0:
        shake_x = random.randint(-shake_intensity, shake_intensity)
        shake_y = random.randint(-shake_intensity, shake_intensity)
        screen_shake -= 1

    # Drawing
    screen.fill(background_color)
    draw_stars()
    draw_particles()
    draw_player_trail()
   
    # Draw obstacles
    for block in blocks:
        if rock_image:
            rotated_image = pygame.transform.rotate(rock_image, block['rotation'])
            screen.blit(rotated_image, (block['x'], block['y']))
        else:
            color = block_colors[obstacle_types.index(block['type']) % len(block_colors)]
            pygame.draw.rect(screen, color, (block['x'], block['y'], block['size'], block['size']))
            pygame.draw.rect(screen, (255, 255, 255), (block['x'], block['y'], block['size'], block['size']), 2)
   
    # Draw boss
    draw_boss()
   
    # Draw power-ups
    for power in power_ups:
        draw_power_up(power)
   
    # Draw player
    if invulnerability_time <= 0 or (invulnerability_time // 5) % 2:
        if player_image:
            screen.blit(player_image, (player_rect.x + shake_x, player_rect.y + shake_y))
        else:
            pygame.draw.rect(screen, (0, 255, 0), 
                           (player_rect.x + shake_x, player_rect.y + shake_y, player_width, player_height))
    
    # Ultimate effect
    if ultimate_active:
        glow_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        glow_alpha = int(100 + 100 * math.sin(game_time * 0.5))
        pygame.draw.circle(glow_surface, (255, 200, 0, glow_alpha), 
                         (player_rect.centerx, player_rect.centery), 200)
        screen.blit(glow_surface, (0, 0))
    
    # Shield effect
    if 'shield' in active_power_ups:
        shield_alpha = int(100 + 155 * math.sin(game_time * 0.2))
        shield_surface = pygame.Surface((player_width + 20, player_height + 20), pygame.SRCALPHA)
        shield_surface.set_alpha(shield_alpha)
        pygame.draw.ellipse(shield_surface, (100, 200, 255),
                          (0, 0, player_width + 20, player_height + 20), 3)
        screen.blit(shield_surface, (player_rect.x - 10 + shake_x, player_rect.y - 10 + shake_y))
   
    # Draw UI
    score_display = f"Score: {player_score}"
    if 'multiplier' in active_power_ups:
        score_display += " x2"
    score_text = font.render(score_display, True, (255, 255, 255))
    screen.blit(score_text, (10, 10))
    
    level_text = font.render(f"Level: {current_level}/{max_levels}", True, (255, 255, 255))
    screen.blit(level_text, (10, 50))
    
    target_text = font.render(f"Target: {winning_scores[current_level - 1]}", True, (200, 200, 255))
    screen.blit(target_text, (10, 90))
    
    lives_text = font.render(f"Lives: {player_lives}", True, (255, 100, 100))
    screen.blit(lives_text, (10, 130))
    
    coins_text = font.render(f"Coins: {coins}", True, (255, 255, 100))
    screen.blit(coins_text, (10, 170))
    
    # Health bar
    bar_width = 200
    bar_height = 20
    bar_x = 10
    bar_y = 210
    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
    health_width = int(bar_width * (player_lives / (max_lives + upgrades['lives'])))
    pygame.draw.rect(screen, (255, 100, 100), (bar_x, bar_y, health_width, bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
    
    # Ultimate charge bar
    ult_bar_width = 200
    ult_bar_height = 15
    ult_bar_x = 10
    ult_bar_y = 240
    pygame.draw.rect(screen, (50, 50, 50), (ult_bar_x, ult_bar_y, ult_bar_width, ult_bar_height))
    ult_width = int(ult_bar_width * (ultimate_charge / max_ultimate_charge))
    ult_color = (255, 200, 0) if ultimate_charge >= max_ultimate_charge else (200, 100, 255)
    pygame.draw.rect(screen, ult_color, (ult_bar_x, ult_bar_y, ult_width, ult_bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (ult_bar_x, ult_bar_y, ult_bar_width, ult_bar_height), 2)
    ult_text = small_font.render("ULTIMATE (Q)", True, (255, 255, 255))
    screen.blit(ult_text, (ult_bar_x, ult_bar_y - 18))
    
    # Combo
    if combo > 0:
        combo_text = font.render(f"Combo: {combo}x", True, (255, 255, 100))
        screen.blit(combo_text, (screen_width - combo_text.get_width() - 10, 10))
    
    # Max combo
    if max_combo > 0:
        max_combo_text = small_font.render(f"Max Combo: {max_combo}x", True, (200, 200, 200))
        screen.blit(max_combo_text, (screen_width - max_combo_text.get_width() - 10, 50))
    
    # Active power-ups
    y_offset = 90
    for power_type, time_left in active_power_ups.items():
        power_names = {
            'shield': 'Shield',
            'speed': 'Speed Boost',
            'slow_motion': 'Slow Motion',
            'multiplier': 'Score x2'
        }
        power_text = small_font.render(f"{power_names[power_type]}: {time_left // 60 + 1}s", True, (200, 255, 200))
        screen.blit(power_text, (screen_width - power_text.get_width() - 10, y_offset))
        y_offset += 25

    pygame.display.flip()

pygame.quit()
