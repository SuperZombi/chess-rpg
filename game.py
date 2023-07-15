import random

class Board:
	def __init__(self, size):
		self.size = size
		self.board = [[None for _ in range(size)] for _ in range(size)]  # Инициализация пустого поля

	def place_hero(self, hero, position):
		x, y = position
		self.board[x][y] = hero
		hero.position = position

	def remove_hero(self, position):
		x, y = position
		hero = self.board[x][y]
		if hero:
			hero.position = None
		self.board[x][y] = None

	def get_visible_for(self, cords, visibility):
		x, y = cords
		visible_cells = []

		if visibility % 2 == 0 or visibility > 4:
			# Круглая видимость
			for dx in range(-visibility, visibility + 1):
				for dy in range(-visibility, visibility + 1):
					if abs(dx) + abs(dy) <= visibility:
						if (8 > x + dx >= 0) and (8 > y + dy >= 0):
							if visibility > 2:
								if not (dx == -visibility and dy == 0) and \
									not (dx == visibility and dy == 0) and \
									not (dx == 0 and dy == -visibility) and \
									not (dx == 0 and dy == visibility): pass
								else:
									continue
							visible_cells.append((x + dx, y + dy))
		else:
			visibility = max(1, visibility-1)
			# Квадратная видимость
			for dx in range(-visibility, visibility+1):
				for dy in range(-visibility, visibility+1):
					if (8 > x + dx >= 0) and (8 > y + dy >= 0):
						if visibility > 1:
							if not (dx == -visibility and dy == -visibility) and \
								not (dx == -visibility and dy == visibility) and \
								not (dx == visibility and dy == -visibility) and \
								not (dx == visibility and dy == visibility): pass
							else:
								continue
						visible_cells.append((x + dx, y + dy))
		
		return visible_cells

	def print_board(self):
		for row in range(self.size):
			for col in range(self.size):
				cell = self.board[row][col]
				if cell is None:
					print("-", end=" ")
				else:
					print(cell.name[0], end=" ")  # Выводим первую букву имени героя
			print()

class Player:
	def __init__(self, name, socket, heroes):
		self.name = name
		self.socket = socket
		self.heroes = heroes

class Game:
	def __init__(self, player1, player2):
		self.board = Board(size=8)
		self.player1 = player1
		self.player2 = player2
		self.current_player = random.choice([player1.name, player2.name])

		self.place_heroes_on_line(self.player1.heroes, player_id=1)
		self.place_heroes_on_line(self.player2.heroes, player_id=2)

	def place_heroes_on_line(self, heroes, player_id):
		line = 0 if player_id == 1 else self.board.size - 1
		positions = [(line, i) for i in range(self.board.size)]  # Список всех позиций на первой линии
		random.shuffle(positions)  # Перемешиваем позиции

		for i, hero in enumerate(heroes):
			x, y = positions[i]
			self.board.place_hero(hero, (x, y))

	def get_player(self, player_id):
		return self.player1 if player_id == self.player1.name else self.player2

	def get_opponent(self, player_id):
		return self.player2 if player_id == self.player1.name else self.player1

	def get_player_heroes(self, player_id):
		return self.get_player(player_id).heroes

	def get_enemy_heroes(self, player_id):
		return self.get_opponent(player_id).heroes

	def get_hero_by_cords(self, player_id, cords):
		heroes = self.get_player_heroes(player_id)
		for hero in heroes:
			if hero.position == tuple(cords):
				return hero

	def get_visible_cells(self, player_id):
		heroes = self.get_player_heroes(player_id)
		visible = []
		for hero in heroes:
			if hero.alive:
				visible += self.board.get_visible_for(hero.position, hero.visibility)
		return list(set(map(tuple, visible)))

	def get_visible_enemies(self, player_id, visability):
		heroes = self.get_enemy_heroes(player_id)
		visible = []
		for hero in heroes:
			if hero.alive and hero.position in visability:
				visible.append(hero)
		return visible

	def is_valid_move(self, player_id, hero, target_position):
		# Проверка, является ли ход героя в пределах его дальности хода
		if not hero.alive: return False
		avalible = self.board.get_visible_for(hero.position, hero.movement_range)
		if tuple(target_position) in avalible:
			all_heroes = self.get_player_heroes(player_id) + self.get_enemy_heroes(player_id)
			for hero in all_heroes:
				if hero.position == tuple(target_position):
					return False
			return True

	def is_valid_attack(self, player_id, hero, target_position):
		# Проверка, находится ли цель в зоне видимости героя и может ли герой атаковать
		if not hero.alive: return False
		avalible = self.board.get_visible_for(hero.position, hero.attack_range)
		if tuple(target_position) in avalible:
			all_heroes = self.get_enemy_heroes(player_id)
			for enemy_hero in all_heroes:
				if enemy_hero.position == tuple(target_position):
					return enemy_hero

	def move_hero(self, player_id, hero, target_position):
		if self.is_valid_move(player_id, hero, target_position):
			self.board.remove_hero(hero.position)
			self.board.place_hero(hero, tuple(target_position))
			return True

	def attack_hero(self, player_id, attacking_hero, target_position):
		target_hero = self.is_valid_attack(player_id, attacking_hero, target_position)
		if target_hero:
			target_hero.hp -= attacking_hero.attack
			if target_hero.hp <= 0:
				target_hero.alive = False
				self.board.remove_hero(target_position)
			return True

	def get_talant(self, hero, talant_name):
		for talant in hero.talantes:
			if talant.name == talant_name:
				return talant

	def use_talant(self, player_id, attacking_hero, talant_name, target_position):
		if not attacking_hero.alive: return False
		talant = self.get_talant(attacking_hero, talant_name)
		if talant:
			if attacking_hero.mana_current >= talant.cost:
				avalible = self.board.get_visible_for(attacking_hero.position, talant.attack_range)
				if tuple(target_position) in avalible:
					if talant.friendly:
						all_heroes = self.get_player_heroes(player_id)
					else:
						all_heroes = self.get_enemy_heroes(player_id)
					for hero in all_heroes:
						if hero.position == tuple(target_position):
							if attacking_hero == hero:
								if not talant.can_use_on_yourself: return False
							attacking_hero.mana_current -= talant.cost
							attacking_hero.mana_current -= attacking_hero.mana_recovery
							hero.addEffect(talant.apply())
							return True

	def check_winer(self):
		count_alive1 = sum(1 for item in self.player1.heroes if item.alive)
		count_alive2 = sum(1 for item in self.player2.heroes if item.alive)
		if count_alive1 == 0:
			return self.player2
		elif count_alive2 == 0:
			return self.player1
		else:
			return False

	def update_talantes(self):
		heroes = self.get_player_heroes(self.current_player)
		for hero in heroes:
			if hero.alive:
				if hasattr(hero, "mana_recovery"):
					hero.mana_current = min(hero.mana_max, hero.mana_current + hero.mana_recovery)
				hero.activateEffects()

	def switch_player(self):
		self.update_talantes()
		winer = self.check_winer()
		if winer:
			return winer
		else:
			self.current_player = self.player2.name if self.current_player == self.player1.name else self.player1.name
