import math
import pygame
import random
import sys

pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Boss Survivor")
clock, FPS = pygame.time.Clock(), 60

# Fonts
font = pygame.font.SysFont(None, 24)
small_font = pygame.font.SysFont(None, 18)

# Game variables
score, game_over, game_paused = 0, False, False
damage_stats, elapsed_time = {}, 0
difficulty_settings = {"Easy": (1, 2000), "Normal": (5, 1500), "Hard": (10, 500)}
difficulty = 'Normal'
initial_enemy_health, spawn_interval = difficulty_settings[difficulty]
spawn_timer, boss_spawn_timer = 0, 0
banana_projectiles, boss_projectiles = [], []
enemy_list, boss_list, banana_collectibles, health_packs = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()

# Phrases for Babuler
babuler_phrases = ["7891347", "adsldasj", "asdjklhja87", "dasda2112"]


# Helper functions
def get_angle(src, dest):
	dx, dy = dest[0] - src[0], dest[1] - src[1]
	return math.atan2(dy, dx)


def clamp(value, min_val, max_val):
	return max(min_val, min(value, max_val))


def draw_text(text, font, color, pos, bg=None):
	txt = font.render(text, True, color)
	if bg:
		bg_rect = txt.get_rect(topleft=pos).inflate(4, 4)
		pygame.draw.rect(screen, bg, bg_rect)
		screen.blit(txt, pos)
	else:
		screen.blit(txt, pos)


# Player class
class Player(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()
		self.base_color = (255, 200, 200)
		self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
		pygame.draw.circle(self.image, self.base_color, (25, 25), 25)
		self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
		self.speed, self.max_health, self.health = 5, 100, 100
		self.level, self.exp, self.exp_to_lvl = 1, 0, 100
		# self.weapons = {'Pistol': Pistol(self)}
		self.weapons = {'SniperRifle': SniperRifle(self)}
		self.orbit_drones = []

	def update(self, keys):
		dx, dy = 0, 0
		if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= self.speed
		if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += self.speed
		if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= self.speed
		if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += self.speed
		self.rect.x, self.rect.y = clamp(self.rect.x + dx, 0, WIDTH - self.rect.width), clamp(self.rect.y + dy, 0,
		                                                                                      HEIGHT - self.rect.height)
		# Update color based on health
		health_ratio = self.health / self.max_health
		self.base_color = (255 * (1 - health_ratio), 200 * health_ratio, 200 * health_ratio)
		self.image.fill((0, 0, 0, 0))
		pygame.draw.circle(self.image, self.base_color, (25, 25), 25)
		# Update weapons
		for w in self.weapons.values():
			w.update()
		# Update drones
		for drone in self.orbit_drones:
			drone.update()

	def add_exp(self, amt):
		self.exp += amt
		while self.exp >= self.exp_to_lvl:
			self.exp -= self.exp_to_lvl
			self.level += 1
			self.exp_to_lvl += 50
			level_up_menu()

	def level_up(self):
		self.add_exp(0)  # Trigger level up if exp >= exp_to_lvl

	def find_nearest_enemy(self):
		enemies = enemy_list.sprites() + boss_list.sprites()
		return min(enemies,
		           key=lambda e: math.hypot(self.rect.centerx - e.rect.centerx, self.rect.centery - e.rect.centery),
		           default=None)


# Weapon classes
class Weapon:
	def __init__(self, player, level=1):
		self.name = "Weapon"
		self.level = level
		self.last_shot = pygame.time.get_ticks()

	def update(self):
		pass

	def fire(self):
		pass

	def upgrade(self):
		self.level += 1
		if self.level == 3:
			self.upgrade_to_super()

	def upgrade_to_super(self):
		pass


class Pistol(Weapon):
	colors = {1: (255, 255, 0), 2: (255, 200, 0), 3: (255, 150, 0)}

	def __init__(self, player, level=1):
		self.name = "Pistol"
		super().__init__(player, level)
		self.shoot_delay, self.damage = max(500 - (level - 1) * 50, 200), 10 + (level - 1) * 5

	def update(self):
		now = pygame.time.get_ticks()

		if now - self.last_shot > self.shoot_delay:
			self.last_shot = now
			self.fire()

	def fire(self):
		if self.level >= 3:
			self.super_fire()
			return

		target = player.find_nearest_enemy()
		if target:
			angle = get_angle(player.rect.center, target.rect.center)
			Projectile(player.rect.centerx, player.rect.centery, angle, self.damage, self.__class__.__name__,
			           color=self.colors.get(self.level, (255, 255, 0))).add_to_group()

	def super_fire(self):
		target = player.find_nearest_enemy()
		if target:
			tmpcenter = list(player.rect.center)
			tmpcenter[0] += 5
			angle = get_angle(tmpcenter, target.rect.center)
			Projectile(player.rect.centerx + 5, player.rect.centery, angle, self.damage, self.__class__.__name__,
			           color=self.colors.get(self.level, (255, 255, 0))).add_to_group()
			tmpcenter[0] -= 10
			angle = get_angle(tmpcenter, target.rect.center)
			Projectile(player.rect.centerx - 5, player.rect.centery, angle, self.damage, self.__class__.__name__,
			           color=self.colors.get(self.level, (255, 255, 0))).add_to_group()


class Shotgun(Weapon):
	def __init__(self, player, level=1):
		self.name = "Shotgun"
		super().__init__(player, level)
		self.shoot_delay, self.damage, self.pellets = max(1500 - (level - 1) * 100, 800), 5 + (level - 1) * 2, 5 + (
				level - 1)

	def update(self):
		now = pygame.time.get_ticks()
		if now - self.last_shot > self.shoot_delay:
			self.last_shot = now
			self.fire()

	def fire(self):
		if self.level >= 3:
			self.super_fire()
			return
		target = player.find_nearest_enemy()
		if target:
			center = get_angle(player.rect.center, target.rect.center)
			for _ in range(self.pellets):
				angle = center + random.uniform(-math.pi / 8, math.pi / 8)
				Projectile(player.rect.centerx, player.rect.centery, angle, self.damage,
				           self.__class__.__name__, color=(139, 69, 19)).add_to_group()

	tmpdelay = 0

	def super_fire(self):
		target = player.find_nearest_enemy()
		if target:
			center = get_angle(player.rect.center, target.rect.center)
			for _ in range(self.pellets):
				angle = center + random.uniform(-math.pi / 8, math.pi / 8)
				Projectile(player.rect.centerx, player.rect.centery, angle, self.damage,
				           self.__class__.__name__, color=(139, 69, 19)).add_to_group()
			if self.shoot_delay != 10:
				self.tmpdelay = self.shoot_delay
				self.shoot_delay = 10
			else:
				self.shoot_delay = self.tmpdelay


class SniperRifle(Weapon):
	def __init__(self, player, level=1):
		self.name = "SniperRifle"
		super().__init__(player, level)
		self.shoot_delay, self.damage, self.speed = max(2000 - (level - 1) * 100, 1000), 150 + (level - 1) * 10, 30

	def update(self):
		now = pygame.time.get_ticks()
		if now - self.last_shot > self.shoot_delay:
			self.last_shot = now
			self.fire()

	def fire(self):
		if self.level >= 1:
			self.super_fire()
			return
		target = player.find_nearest_enemy()
		if target:
			angle = get_angle(player.rect.center, target.rect.center)
			SniperBullet(player.rect.centerx, player.rect.centery, angle, self.damage,
			             self.__class__.__name__, speed=self.speed).add_to_group()

	def super_fire(self):
		target = player.find_nearest_enemy()
		if target:
			angle = get_angle(player.rect.center, target.rect.center)
			SuperSniperBullet(player.rect.centerx,
			                  player.rect.centery, angle, self.damage,
			                  self.__class__.__name__, speed=self.speed).add_to_group()


class RocketLauncher(Weapon):
	def __init__(self, player, level=1):
		self.name = "RocketLauncher"
		super().__init__(player, level)
		self.shoot_delay, self.damage = max(3000 - (level - 1) * 200, 1500), 300 + (level - 1) * 20

	def update(self):
		now = pygame.time.get_ticks()
		if now - self.last_shot > self.shoot_delay:
			self.last_shot = now
			self.fire()

	def fire(self):
		if self.level >= 3:
			self.super_fire()
			return
		target = player.find_nearest_enemy()
		if target:
			angle = get_angle(player.rect.center, target.rect.center)
			HomingRocket(player.rect.centerx, player.rect.centery, angle, self.damage,
			             self.__class__.__name__).add_to_group()

	def super_fire(self):
		HomingRocket(player.rect.centerx, player.rect.centery,
		             get_angle(player.rect.center, (random.randint(0, WIDTH), random.randint(0, HEIGHT))),
		             self.damage, self.__class__.__name__).add_to_group()


class Rifle(Weapon):
	def __init__(self, player, level=1):
		self.name = "Rifle"
		super().__init__(player, level)
		self.shoot_delay, self.damage = max(200 - (level - 1) * 10, 50), 8 + (level - 1) * 2

	def update(self):
		now = pygame.time.get_ticks()
		if now - self.last_shot > self.shoot_delay:
			self.last_shot = now
			self.fire()

	def fire(self):
		if self.level >= 3:
			self.super_fire()
			return
		target = player.find_nearest_enemy()
		if target:
			angle = get_angle(player.rect.center, target.rect.center)
			Projectile(player.rect.centerx, player.rect.centery, angle, self.damage, self.__class__.__name__,
			           color=(0, 255, 0)).add_to_group()

	def super_fire(self):
		Projectile(player.rect.centerx, player.rect.centery,
		           get_angle(player.rect.center, (random.randint(0, WIDTH), random.randint(0, HEIGHT))),
		           self.damage, self.__class__.__name__, color=(0, 255, 0), pierce=True).add_to_group()


class MachineGun(Weapon):
	def __init__(self, player, level=1):
		self.name = "MachineGun"
		super().__init__(player, level)
		self.shoot_delay, self.damage = max(100 - (level - 1) * 5, 20), 5 + (level - 1)

	def update(self):
		now = pygame.time.get_ticks()
		if now - self.last_shot > self.shoot_delay:
			self.last_shot = now
			self.fire()

	def fire(self):
		damage = self.damage
		if self.level >= 3:
			damage *= 2
		target = player.find_nearest_enemy()
		if target:
			angle = get_angle(player.rect.center, target.rect.center)

			Projectile(player.rect.centerx, player.rect.centery, angle, damage, self.__class__.__name__,
			           color=(0, 0, 255)).add_to_group()


class Sword(Weapon):
	def __init__(self, player, level=1):
		self.name = "Sword"
		super().__init__(player, level)
		self.damage, self.range = 20 + (level - 1) * 5, 50 + (level - 1) * 10

	def update(self):
		self_range = self.range
		if self.level >= 3:
			self_range += 10
		for enemy in enemy_list:
			if math.hypot(player.rect.centerx - enemy.rect.centerx,
			              player.rect.centery - enemy.rect.centery) <= self_range:
				enemy.health -= self.damage
				if enemy.health <= 0:
					enemy.kill()
					player.add_exp(20)
				damage_stats[self.__class__.__name__] = damage_stats.get(self.__class__.__name__, 0) + self.damage
		for boss in boss_list:
			if math.hypot(player.rect.centerx - boss.rect.centerx,
			              player.rect.centery - boss.rect.centery) <= self_range:
				boss.health -= self.damage
				if boss.health <= 0:
					boss.kill()
					player.add_exp(200)
				damage_stats[self.__class__.__name__] = damage_stats.get(self.__class__.__name__, 0) + self.damage

	def fire(self):
		pass

	def super_fire(self):
		self.damage += 10


class Drone(Weapon):
	def __init__(self, player, level=1):
		self.name = "Drone"
		super().__init__(player, level)
		self.orbit_radius = 100 + (level - 1) * 20
		self.angle = 0
		self.speed = 0.05
		self.damage = 5 + (level - 1) * 2
		self.super_drone = False

	def update(self):
		if self.level >= 3 and not self.super_drone:
			self.super_drone = True
			self.damage += 5

		self.angle += self.speed
		x = player.rect.centerx + self.orbit_radius * math.cos(self.angle)
		y = player.rect.centery + self.orbit_radius * math.sin(self.angle)
		drone_sprite = DroneSprite(x, y, self.damage, "Drone", super_drone=self.super_drone)
		drone_sprite.add_to_group()

	def super_fire(self):
		self.damage += 5


class SuperPistol(Pistol):
	def __init__(self, player, level=3):
		super().__init__(player, level)
		self.damage = 20
		self.shoot_delay = max(400 - (level - 3) * 50, 200)
		self.name = "Super Pistol"

	def fire(self):
		target = player.find_nearest_enemy()
		if target:
			angle = get_angle(player.rect.center, target.rect.center)

			for offset in [-0.05, 0.05]:
				bullet = Projectile(
					player.rect.centerx,
					player.rect.centery,
					angle + offset,
					self.damage,
					self.name,
					color=(255, 215, 0)
				)
				bullet.add_to_group()


class SuperShotgun(Shotgun):
	def __init__(self, player, level=3):
		super().__init__(player, level)
		self.pellets = 10
		self.shoot_delay = max(1200 - (level - 3) * 100, 600)
		self.name = "Super Shotgun"

	def fire(self):
		target = player.find_nearest_enemy()
		if target:
			center = get_angle(player.rect.center, target.rect.center)
			for _ in range(self.pellets):
				angle = center + random.uniform(-math.pi / 12, math.pi / 12)
				bullet = Projectile(
					player.rect.centerx,
					player.rect.centery,
					angle,
					self.damage,
					self.name,
					color=(139, 69, 19)
				)
				bullet.add_to_group()


# Projectile classes
class Projectile(pygame.sprite.Sprite):
	def __init__(self, x, y, angle, damage, weapon, color=(255, 255, 0), speed=10, pierce=False):
		super().__init__()
		self.image = pygame.Surface((10, 10))
		self.image.fill(color)
		self.rect = self.image.get_rect(center=(x, y))
		self.angle, self.speed, self.damage, self.weapon, self.pierce = angle, speed, damage, weapon, pierce

	def update(self):
		self.rect.x += math.cos(self.angle) * self.speed
		self.rect.y += math.sin(self.angle) * self.speed
		if not screen.get_rect().collidepoint(self.rect.center):
			self.kill()
		else:
			hits = pygame.sprite.spritecollide(self, enemy_list, False) + pygame.sprite.spritecollide(self, boss_list,
			                                                                                          False)
			for enemy in hits:
				enemy.health -= self.damage
				damage_stats[self.weapon] = damage_stats.get(self.weapon, 0) + self.damage
				if enemy.health <= 0:
					enemy.kill()
					player.add_exp(20 if isinstance(enemy, Enemy) else 200)
				if not self.pierce:
					self.kill()
					break

	def add_to_group(self):
		projectiles.add(self)
		pass


class SniperBullet(Projectile):
	def __init__(self, x, y, angle, damage, weapon, color=(0, 255, 0), speed=30):
		super().__init__(x, y, angle, damage, weapon, color, speed, pierce=True)
		self.max_trace_length = 50
		self.trace = []

	def update(self):
		super().update()


class SuperSniperBullet(Projectile):
	def __init__(self, x, y, angle, damage, weapon, color=(0, 255, 0), speed=30):
		super().__init__(x, y, angle, damage, weapon, color, speed, pierce=True)
		self.trace = []
		self.max_trace_length = 15

	def find_nearest_enemy(self):
		enemies = enemy_list.sprites() + boss_list.sprites()
		return min(enemies,
		           key=lambda e: math.hypot(self.rect.centerx - e.rect.centerx, self.rect.centery - e.rect.centery),
		           default=None)

	def update(self):
		target = self.find_nearest_enemy()

		if target:
			desired_angle = get_angle(self.rect.center, target.rect.center)
			angle_difference = desired_angle - self.angle

			angle_difference = (angle_difference + math.pi) % (2 * math.pi) - math.pi
			max_turn_rate = 0.3
			if angle_difference > max_turn_rate:
				angle_change = max_turn_rate
			elif angle_difference < -max_turn_rate:
				angle_change = -max_turn_rate
			else:
				angle_change = angle_difference
			self.angle += angle_change

		self.rect.x += math.cos(self.angle) * self.speed
		self.rect.y += math.sin(self.angle) * self.speed

		self.trace.append(self.rect.center)
		if len(self.trace) > self.max_trace_length:
			self.trace.pop(0)

		if not screen.get_rect().collidepoint(self.rect.center):
			self.kill()
		else:
			hits = pygame.sprite.spritecollide(self, enemy_list, False) + pygame.sprite.spritecollide(self, boss_list,
			                                                                                          False)
			for enemy in hits:
				enemy.health -= self.damage
				damage_stats[self.weapon] = damage_stats.get(self.weapon, 0) + self.damage
				if enemy.health <= 0:
					enemy.kill()
					player.add_exp(20 if isinstance(enemy, Enemy) else 200)
				if not self.pierce:
					self.kill()
					break

	def add_to_group(self):
		projectiles.add(self)


# Add trace effect or change trajectory if super
# For simplicity, omitted


class HomingRocket(Projectile):
	def __init__(self, x, y, angle, damage, weapon, color=(255, 165, 0), speed=7):
		super().__init__(x, y, angle, damage, weapon, color, speed)
		self.target = player.find_nearest_enemy()
		self.explosion_radius = 50

	def update(self):
		if self.target and self.target.alive():
			self.angle = get_angle(self.rect.center, self.target.rect.center)
		super().update()
		hits = pygame.sprite.spritecollide(self, enemy_list, False) + pygame.sprite.spritecollide(self, boss_list,
		                                                                                          False)
		if hits:
			Explosion(self.rect.centerx, self.rect.centery, self.explosion_radius, self.damage,
			          self.weapon).add_to_group()
			self.kill()


class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, radius, damage, weapon):
		super().__init__()
		self.radius, self.damage, self.weapon = radius, damage, weapon
		self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
		pygame.draw.circle(self.image, (255, 0, 0, 128), (radius, radius), radius)
		self.rect = self.image.get_rect(center=(x, y))
		self.timer = pygame.time.get_ticks()

	def update(self):
		if pygame.time.get_ticks() - self.timer > 500:
			self.kill()
		else:
			hits = pygame.sprite.spritecollide(self, enemy_list, False) + pygame.sprite.spritecollide(self, boss_list,
			                                                                                          False)
			for enemy in hits:
				enemy.health -= self.damage
				damage_stats[self.weapon] = damage_stats.get(self.weapon, 0) + self.damage
				if enemy.health <= 0:
					enemy.kill()
					player.add_exp(20 if isinstance(enemy, Enemy) else 200)

	def add_to_group(self):
		explosions.add(self)


class DroneSprite(pygame.sprite.Sprite):
	def __init__(self, x, y, damage, weapon, super_drone=False):
		super().__init__()
		size = 20 if not super_drone else 30
		self.image = pygame.Surface((size, size), pygame.SRCALPHA)
		color = (0, 255, 255) if not super_drone else (255, 0, 255)
		pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
		self.rect = self.image.get_rect(center=(x, y))
		self.damage = damage
		self.weapon = weapon

	def update(self):
		hits = pygame.sprite.spritecollide(self, enemy_list, False) + pygame.sprite.spritecollide(self, boss_list,
		                                                                                          False)
		for enemy in hits:
			enemy.health -= self.damage
			damage_stats[self.weapon] = damage_stats.get(self.weapon, 0) + self.damage
			if enemy.health <= 0:
				enemy.kill()
				player.add_exp(20 if isinstance(enemy, Enemy) else 200)

	def add_to_group(self):
		drones.add(self)


class BossProjectile(pygame.sprite.Sprite):
	def __init__(self, x, y, angle, text=None):
		super().__init__()
		if text:
			self.font = pygame.font.SysFont(None, 20)
			self.image = self.font.render(text, True, (255, 255, 255))
			self.bg = pygame.Surface(self.image.get_size())
			self.bg.fill((0, 0, 0))
			self.bg.blit(self.image, (0, 0))
			self.image = self.bg
		else:
			self.image = pygame.Surface((15, 15))
			self.image.fill((150, 0, 150))
		self.rect = self.image.get_rect(center=(x, y))
		self.angle, self.speed = angle, 3

	def update(self):
		self.rect.x += math.cos(self.angle) * self.speed
		self.rect.y += math.sin(self.angle) * self.speed
		if not screen.get_rect().collidepoint(self.rect.center):
			self.kill()
		if self.rect.colliderect(player.rect):
			player.health -= 15
			self.kill()
			if player.health <= 0:
				global game_over
				game_over = True

	def add_to_group(self):
		boss_projectiles_group.add(self)


class BabulerProjectile(BossProjectile):
	def __init__(self, x, y, target_pos, text):
		angle = get_angle((x, y), target_pos)
		super().__init__(x, y, angle, text)

	def update(self):
		super().update()


# Enemy classes
class Enemy(pygame.sprite.Sprite):
	def __init__(self, health):
		super().__init__()
		self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
		pygame.draw.circle(self.image, (200, 0, 0), (20, 20), 20)
		self.rect = self.image.get_rect()
		edge = random.choice(['top', 'bottom', 'left', 'right'])
		if edge == 'top':
			self.rect.centerx, self.rect.y = random.randint(0, WIDTH), 0
		elif edge == 'bottom':
			self.rect.centerx, self.rect.y = random.randint(0, WIDTH), HEIGHT
		elif edge == 'left':
			self.rect.x, self.rect.centery = 0, random.randint(0, HEIGHT)
		else:
			self.rect.x, self.rect.centery = WIDTH, random.randint(0, HEIGHT)
		self.speed, self.health = 2, health

	def update(self, player_pos):
		angle = get_angle(self.rect.center, player_pos)
		self.rect.x += math.cos(angle) * self.speed
		self.rect.y += math.sin(angle) * self.speed
		if self.rect.colliderect(player.rect):
			player.health -= 10
			self.kill()
			if player.health <= 0:
				global game_over
				game_over = True


class BossEnemy(pygame.sprite.Sprite):
	def __init__(self, health):
		super().__init__()
		self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
		pygame.draw.circle(self.image, (255, 100, 100), (30, 30), 30)
		self.rect = self.image.get_rect()
		edge = random.choice(['top', 'bottom', 'left', 'right'])
		if edge == 'top':
			self.rect.centerx, self.rect.y = random.randint(0, WIDTH), 0
		elif edge == 'bottom':
			self.rect.centerx, self.rect.y = random.randint(0, WIDTH), HEIGHT
		elif edge == 'left':
			self.rect.x, self.rect.centery = 0, random.randint(0, HEIGHT)
		else:
			self.rect.x, self.rect.centery = WIDTH, random.randint(0, HEIGHT)
		self.speed, self.health, self.max_health = 1.5, health, health
		self.last_shot, self.shoot_delay = pygame.time.get_ticks(), 2000
		self.name = "Boss"

	def update(self, player_pos):
		angle = get_angle(self.rect.center, player_pos)
		self.rect.x += math.cos(angle) * self.speed
		self.rect.y += math.sin(angle) * self.speed
		now = pygame.time.get_ticks()
		if now - self.last_shot > self.shoot_delay:
			self.last_shot = now
			angle = get_angle(self.rect.center, player_pos)
			BossProjectile(self.rect.centerx, self.rect.centery, angle).add_to_group()
		if self.rect.colliderect(player.rect):
			player.health -= 20
			if player.health <= 0:
				global game_over
				game_over = True


class BabulerBoss(BossEnemy):
	def __init__(self, health):
		super().__init__(health * 10)
		self.name = "babuler"
		self.image.fill((100, 100, 255))
		self.shoot_delay = 1500

	def shoot(self, player_pos):
		phrase = random.choice(babuler_phrases)
		BabulerProjectile(self.rect.centerx, self.rect.centery, player_pos, phrase).add_to_group()


# Collectibles
class BananaCollectible(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()
		self.image = pygame.Surface((20, 40), pygame.SRCALPHA)
		pygame.draw.ellipse(self.image, (255, 255, 0), [0, 0, 20, 40])
		self.rect = self.image.get_rect(center=(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)))

	def update(self):
		pass


class HealthPack(pygame.sprite.Sprite):
	def __init__(self):
		super().__init__()
		self.font = pygame.font.SysFont(None, 18)
		self.text = self.font.render('hp', True, (255, 255, 255))
		self.bg = pygame.Surface(self.text.get_size())
		self.bg.fill((0, 255, 0))
		self.bg.blit(self.text, (0, 0))
		self.image = self.bg
		self.rect = self.image.get_rect(center=(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)))

	def update(self):
		if self.rect.colliderect(player.rect):
			player.health = clamp(player.health + 30, 0, player.max_health)
			self.kill()


# Explosion effect
class ExplosionEffect(pygame.sprite.Sprite):
	def __init__(self, x, y):
		super().__init__()
		self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
		pygame.draw.circle(self.image, (255, 165, 0), (25, 25), 25)
		self.rect = self.image.get_rect(center=(x, y))
		self.timer = pygame.time.get_ticks()

	def update(self):
		if pygame.time.get_ticks() - self.timer > 500:
			self.kill()


# Groups
projectiles = pygame.sprite.Group()
boss_projectiles_group = pygame.sprite.Group()
explosions = pygame.sprite.Group()
drones = pygame.sprite.Group()
collectibles = pygame.sprite.Group()
healthpacks = pygame.sprite.Group()


def add_weapon_to_player(name):
	if name in player.weapons:
		player.weapons[name].upgrade()
	else:
		weapon_classes = {"Pistol": Pistol, "Shotgun": Shotgun, "SniperRifle": SniperRifle,
		                  "RocketLauncher": RocketLauncher, "Rifle": Rifle, "MachineGun": MachineGun, "Sword": Sword,
		                  "Drone": Drone}
		player.weapons[name] = weapon_classes[name](player)


def difficulty_menu():
	global difficulty, initial_enemy_health, spawn_interval
	menu = True
	while menu:
		clock.tick(FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT: pygame.quit(); sys.exit()
		screen.fill((0, 0, 0))
		draw_text('diff', font, (255, 255, 0), (WIDTH // 2 - 100, HEIGHT // 2 - 100))
		for i, diff in enumerate(["Easy", "Normal", "Hard"]):
			draw_text(f'{i + 1}: {diff}', font, (255, 255, 255), (WIDTH // 2 - 50, HEIGHT // 2 - 50 + i * 40))
		pygame.display.flip()
		keys = pygame.key.get_pressed()
		for i in range(3):
			if keys[getattr(pygame, f'K_{i + 1}')]:
				difficulty = ["Easy", "Normal", "Hard"][i]
				initial_enemy_health, spawn_interval = difficulty_settings[difficulty]
				menu = False


def level_up_menu():
	global game_paused
	game_paused = True
	choices = random.sample(
		["Pistol", "Shotgun", "SniperRifle", "RocketLauncher", "Rifle", "MachineGun", "Sword", "Drone"], 3)
	while True:
		clock.tick(FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT: pygame.quit(); sys.exit()
		screen.fill((0, 0, 0))
		draw_text('choose  weapon', font, (255, 255, 0), (WIDTH // 2 - 50, HEIGHT // 2 - 100))
		for i, weapon in enumerate(choices):
			draw_text(f'{i + 1}: {weapon}', font, (255, 255, 255), (WIDTH // 2 - 50, HEIGHT // 2 - 50 + i * 40))
		pygame.display.flip()
		keys = pygame.key.get_pressed()
		for i in range(len(choices)):
			if keys[getattr(pygame, f'K_{i + 1}')]:
				add_weapon_to_player(choices[i])
				game_paused = False
				return


def display_stats():
	while True:
		clock.tick(FPS)
		for event in pygame.event.get():
			if event.type == pygame.QUIT: pygame.quit(); sys.exit()
		screen.fill((0, 0, 0))
		draw_text('Stat', font, (255, 255, 0), (WIDTH // 2 - 60, 50))
		for i, (w, d) in enumerate(damage_stats.items()):
			draw_text(f'{w}: {d} dmg', font, (255, 255, 255), (WIDTH // 2 - 60, 100 + i * 30))
		pygame.display.flip()


difficulty_menu()
player = Player()

# Main game loop
running = True
game_start_time = pygame.time.get_ticks()
while running:
	clock.tick(FPS)
	keys = pygame.key.get_pressed()
	for event in pygame.event.get():
		if event.type == pygame.QUIT: running = False
	if not game_over and not game_paused:
		now = pygame.time.get_ticks()
		elapsed_time = (now - game_start_time) // 1000
		player.update(keys)
		enemy_list.update(player.rect.center)
		boss_list.update(player.rect.center)
		projectiles.update()
		boss_projectiles_group.update()
		explosions.update()
		drones.update()
		collectibles.update()
		healthpacks.update()
		# Spawn enemies
		if now - spawn_timer > spawn_interval - (15 * elapsed_time):
			spawn_timer = now
			health = initial_enemy_health + (elapsed_time ** 1.1)
			enemy_list.add(Enemy(health))
		# Spawn bosses every 30 sec
		if now - boss_spawn_timer > 30000 and not boss_list:
			boss_spawn_timer = now
			boss = BabulerBoss(5) if random.choice([True, False]) else BossEnemy(50)
			boss_list.add(boss)
		# Spawn collectibles
		if random.randint(0, 500) < 5: collectibles.add(BananaCollectible())
		# Spawn health packs
		if random.randint(0, 1000) < 3: healthpacks.add(HealthPack())
		# Check collectibles
		for banana in collectibles:
			if player.rect.colliderect(banana.rect):
				player.add_exp(10)
				banana.kill()
		# Check health packs
		for pack in healthpacks:
			if player.rect.colliderect(pack.rect):
				pack.update()
		# Collision handled in projectile classes
		# Spawn bonuses after boss defeat
		for boss in boss_list:
			if not boss.alive():
				bonuses = 3 if isinstance(boss, BabulerBoss) else 1
				for _ in range(bonuses):
					HealthPack().add()
	# Draw
	screen.fill((100, 100, 100))
	player_group = pygame.sprite.Group(player)
	player_group.draw(screen)
	enemy_list.draw(screen)
	boss_list.draw(screen)
	projectiles.draw(screen)
	boss_projectiles_group.draw(screen)
	explosions.draw(screen)
	drones.draw(screen)
	collectibles.draw(screen)
	healthpacks.draw(screen)
	for projectile in projectiles:
		if isinstance(projectile, SuperSniperBullet):
			for i, pos in enumerate(projectile.trace):
				alpha = int(255 * (i + 1) / len(projectile.trace))
				trace_color = (0, 255, 0, alpha)
				trace_surface = pygame.Surface((4, 4), pygame.SRCALPHA)
				pygame.draw.circle(trace_surface, trace_color, (2, 2), 2)
				screen.blit(trace_surface, (pos[0] - 2, pos[1] - 2))
	# Draw timer
	draw_text(f'Time: {elapsed_time}s', small_font, (255, 255, 255), (WIDTH // 2 - 30, 10))
	# Draw UI
	draw_text(f'HP: {player.health}/{player.max_health}', small_font, (255, 255, 255), (10, 10))
	draw_text(f'LVL: {player.level}', small_font, (255, 255, 255), (10, 30))
	draw_text(f'EXP: {player.exp}/{player.exp_to_lvl}', small_font, (255, 255, 255), (10, 50))
	draw_text(f'DIFF: {difficulty}', small_font, (255, 255, 255), (10, 70))
	# Draw weapons
	for i, (w, weapon) in enumerate(player.weapons.items()):
		draw_text(f'{w} Lvl {weapon.level}', small_font, (255, 255, 255), (WIDTH - 150, HEIGHT - 20 - i * 20))
	# Game Over
	if game_over:
		draw_text('Game over! Press R to restart', font, (255, 0, 0), (WIDTH // 2 - 150, HEIGHT // 2))
		if keys[pygame.K_r]:
			player = Player()
			score, game_over, elapsed_time = 0, False, 0
			enemy_list.empty()
			boss_list.empty()
			projectiles.empty()
			boss_projectiles_group.empty()
			explosions.empty()
			drones.empty()
			collectibles.empty()
			healthpacks.empty()
			damage_stats.clear()
			game_start_time = pygame.time.get_ticks()
			difficulty_menu()
		else:
			display_stats()
	pygame.display.flip()
pygame.quit()
sys.exit()
