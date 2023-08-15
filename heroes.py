class Talant:
	def __init__(self, name, from_player=None, from_hero=None, event_worker=None):
		self.name = name
		self.friendly = False
		self.from_player = from_player
		self.from_hero = from_hero
		self.new_event = event_worker

	async def apply(self, from_player=None, from_hero=None, target_hero=None, event_worker=None):
		return self.__class__()

	def __repr__(self):
		return "Effect." + self.name

class Bleeding(Talant):
	def __init__(self, damage, repeats, cost=0, attack_range=None, **kwargs):
		super().__init__("Bleeding", **kwargs)
		self.damage = damage
		self.repeats = repeats
		self.cost = cost
		self.attack_range = attack_range
		self.icon = "images/bleeding.svg"

	async def apply(self, from_player, from_hero, target_hero, event_worker):
		effect = self.__class__(damage=self.damage, repeats=self.repeats,
								from_player=from_player, from_hero=from_hero, event_worker=event_worker)
		target_hero.addEffect(effect)
		return effect

	async def activate(self, hero):
		hero.hp = max(0, hero.hp - self.damage)
		await self.new_event(self.from_player, self.from_hero, hero, "damage_by_effect", self)
		self.repeats = max(0, self.repeats - 1)
		if hero.hp == 0:
			hero.alive = False
			await self.new_event(self.from_player, self.from_hero, hero, "kill", self)
		return self.repeats == 0

class Healing(Talant):
	def __init__(self, hp, repeats, cost=0, attack_range=None, **kwargs):
		super().__init__("Healing", **kwargs)
		self.friendly = True
		self.can_use_on_yourself = False
		self.hp = hp
		self.repeats = repeats
		self.cost = cost
		self.attack_range = attack_range
		self.icon = "images/potion.png"

	async def apply(self, from_player, from_hero, target_hero, event_worker):
		effect = self.__class__(hp=self.hp, repeats=self.repeats,
							from_player=from_player, from_hero=from_hero, event_worker=event_worker)
		target_hero.addEffect(effect)
		return effect

	async def activate(self, hero):
		hero.hp = min(hero.max_hp, hero.hp + self.hp)
		await self.new_event(self.from_player, self.from_hero, hero, "heal_by_effect", self, friendly=True)
		self.repeats = max(0, self.repeats - 1)
		return self.repeats == 0

class Vampirism(Talant):
	def __init__(self, damage, hp, cost=0, attack_range=None):
		super().__init__("Vampire's bite")
		self.damage = damage
		self.hp = hp
		self.cost = cost
		self.attack_range = attack_range
		self.icon = "images/fangs.svg"

	async def apply(self, from_player, from_hero, target_hero, event_worker):
		from_hero.hp = min(from_hero.max_hp, from_hero.hp + self.hp)
		target_hero.hp = max(0, target_hero.hp - self.damage)
		await event_worker(from_player, from_hero, from_hero, "heal_by_effect", self, friendly=True)
		await event_worker(from_player, from_hero, target_hero, "damage_by_effect", self)
		if target_hero.hp == 0:
			target_hero.alive = False
			await event_worker(from_player, from_hero, target_hero, "kill", self)

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

	async def activateEffects(self):
		new_effects = []
		for effect in self.effects:
			if self.alive:
				need_remove = await effect.activate(self)
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

class Dracula(Hero):
	def __init__(self):
		super().__init__("Dracula", hp=3)
		self.attack = 2
		self.visibility = 2
		self.movement_range = 1
		self.attack_range = 3
		self.talantes = [
			Vampirism(damage=1, hp=1, attack_range=3)
		]
		self.icon = "/images/vampire.svg"
