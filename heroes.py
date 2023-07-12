class Hero:
	def __init__(self, name, attack, hp):
		self.alive = True
		self.name = name
		self.attack = attack  # Сила атаки героя
		self.hp = hp  # Здоровье героя
		self.max_hp = hp  # Здоровье героя
		self.visibility = None  # Радиус видимости героя
		self.movement_range = None  # Дальность хода героя
		self.attack_range = None  # Дальность атаки
		self.position = None  # Позиция героя на игровом поле
		self.icon = None

class Ninja(Hero):
	def __init__(self):
		super().__init__("Ninja", attack=1, hp=4)
		self.visibility = 3
		self.movement_range = 2
		self.attack_range = 3
		self.icon = "/images/ninja.png"

class Damager(Hero):
	def __init__(self):
		super().__init__("Damager", attack=3, hp=6)
		self.visibility = 2
		self.movement_range = 1
		self.attack_range = 2
		self.icon = "/images/skeleton.png"

class Tank(Hero):
	def __init__(self):
		super().__init__("Tank", attack=2, hp=10)
		self.visibility = 1
		self.movement_range = 1
		self.attack_range = 1
		self.icon = "/images/iron-man.png"
