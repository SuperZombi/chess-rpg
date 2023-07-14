class Talant:
	def __init__(self, name):
		self.name = name
		self.friendly = False

	def apply(self):
		return self.__class__()

class Bleeding(Talant):
	def __init__(self, damage, repeats, cost=0, attack_range=None):
		super().__init__("Bleeding")
		self.damage = damage
		self.repeats = repeats
		self.cost = cost
		self.attack_range = attack_range
		self.icon = "images/bleeding.svg"

	def apply(self):
		return self.__class__(damage=self.damage, repeats=self.repeats)

	def activate(self, hero):
		hero.hp = max(0, hero.hp - self.damage)
		self.repeats = max(0, self.repeats - 1)
		if hero.hp == 0:
			hero.alive = False
		return self.repeats == 0

class Healing(Talant):
	def __init__(self, hp, repeats, cost=0, attack_range=None):
		super().__init__("Healing")
		self.friendly = True
		self.can_use_on_yourself = False
		self.hp = hp
		self.repeats = repeats
		self.cost = cost
		self.attack_range = attack_range
		self.icon = "images/potion.png"

	def apply(self):
		return self.__class__(hp=self.hp, repeats=self.repeats)

	def activate(self, hero):
		hero.hp = min(hero.max_hp, hero.hp + self.hp)
		self.repeats = max(0, self.repeats - 1)
		return self.repeats == 0

#################################

class Hero:
	def __init__(self, name, hp):
		self.alive = True
		self.name = name
		self.hp = hp  # Здоровье героя
		self.max_hp = hp  # Здоровье героя
		self.attack = None  # Сила атаки героя
		self.visibility = None  # Радиус видимости героя
		self.movement_range = None  # Дальность хода героя
		self.attack_range = None  # Дальность атаки
		self.position = None  # Позиция героя на игровом поле
		self.icon = None
		self.effects = []

	def __repr__(self):
		return "Hero." + self.name

	def new(self):
		return self.__class__()

	def addEffect(self, effect):
		self.effects.append(effect)

	def activateEffects(self):
		new_effects = []
		for effect in self.effects:
			if self.alive:
				need_remove = effect.activate(self)
				if not need_remove:
					new_effects.append(effect)
		self.effects = new_effects

class Ninja(Hero):
	def __init__(self):
		super().__init__("Ninja", hp=4)
		self.attack = 1
		self.visibility = 3
		self.movement_range = 2
		self.attack_range = 3
		self.icon = "/images/ninja.png"

class Damager(Hero):
	def __init__(self):
		super().__init__("Damager", hp=6)
		self.attack = 3
		self.visibility = 2
		self.movement_range = 1
		self.attack_range = 4
		self.icon = "/images/skeleton.png"

class Tank(Hero):
	def __init__(self):
		super().__init__("Tank", hp=8)
		self.attack = 2
		self.visibility = 1
		self.movement_range = 1
		self.attack_range = 2
		self.icon = "/images/iron-man.png"

class Wizard(Hero):
	def __init__(self):
		super().__init__("Wizard", hp=4)
		self.attack = 1
		self.visibility = 1
		self.movement_range = 1
		self.attack_range = 1

		self.mana_current = 0
		self.mana_max = 2
		self.mana_recovery = 0.5
		self.talantes = [
			Bleeding(damage=1, repeats=2, cost=2, attack_range=4),
			Healing(hp=1, repeats=1, cost=2, attack_range=4),
		]
		self.icon = "/images/wizard.png"
