class Hero:
	def __init__(self, name, visibility, attack, hp, movement_range):
		self.name = name
		self.visibility = visibility  # Зона видимости героя
		self.attack = attack  # Сила атаки героя
		self.hp = hp  # Здоровье героя
		self.max_hp = hp  # Здоровье героя
		self.movement_range = movement_range  # Дальность хода героя
		self.position = None  # Позиция героя на игровом поле
		self.icon = None

class Ninja(Hero):
	def __init__(self):
		super().__init__("Ninja", visibility=3, attack=1, hp=4, movement_range=2)
		self.icon = "/images/ninja.png"

class Damager(Hero):
	def __init__(self):
		super().__init__("Damager", visibility=2, attack=3, hp=6, movement_range=1)
		self.icon = "/images/skeleton.png"

class Tank(Hero):
	def __init__(self):
		super().__init__("Tank", visibility=1, attack=2, hp=10, movement_range=1)
		self.icon = "/images/iron-man.png"
