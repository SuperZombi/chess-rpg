from heroes import *
from game import *

import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi import Request
import uvicorn
from pydantic import BaseModel

app = FastAPI()

# Инициализация игры
game = None

@app.get("/", response_class=FileResponse)
def home():
	return FileResponse("data/index.html")

@app.get("/{_:path}", response_class=FileResponse)
async def data(request: Request):
	path = request.url.path[1:]
	filepath = os.path.join("data", path)
	return FileResponse(filepath)


@app.post("/api/new_game")
async def start_game():
	global game
	your_player_id = 2
	players = {
		1: [Ninja(), Damager(), Tank()],
		2: [Ninja(), Damager(), Tank()]
	}
	game = Game(players[1], players[2])
	game.board.print_board()
	player_heroes = game.get_player_heroes(your_player_id)
	visible = game.get_visible_cells(your_player_id)
	
	return {"your_player_id": your_player_id, "now_turn": game.current_player, "heroes": player_heroes, "board": visible}


class move_hero_model(BaseModel):
	player_id: int
	old_cords: list
	new_cords: list

@app.post("/api/move_hero")
async def move_hero(args: move_hero_model):
	if game.current_player == args.player_id:
		hero = game.get_hero_by_cords(args.player_id, args.old_cords)
		if hero:
			if game.move_hero(args.player_id, hero, args.new_cords):
				game.board.print_board()
				# game.switch_player()

				player_heroes = game.get_player_heroes(args.player_id)
				visible = game.get_visible_cells(args.player_id)
				enemies = game.get_visible_enemies(args.player_id, visible)
				return {"success": True, "now_turn": game.current_player, "heroes": player_heroes, "enemies": enemies, "board": visible}
	return {"success": False}


@app.post("/attack_hero")
async def attack_hero(player_id: int, attacking_hero_id: int, target_x: int, target_y: int):
	player = game.player1_heroes if player_id == 1 else game.player2_heroes
	attacking_hero = player[attacking_hero_id]
	game.attack_hero(attacking_hero, (target_x, target_y))
	game.switch_player()
	return {"message": "Hero attacked!"}


@app.get("/game_status")
async def game_status():
	# Возвращаем текущее состояние игры, информацию о героях и поле
	status = {
		"current_player": game.current_player,
		"player1_heroes": [],
		"player2_heroes": [],
		"board": []
	}

	for hero in game.player1_heroes:
		status["player1_heroes"].append({
			"name": hero.name,
			"position": hero.position,
			"hp": hero.hp
		})

	for hero in game.player2_heroes:
		status["player2_heroes"].append({
			"name": hero.name,
			"position": hero.position,
			"hp": hero.hp
		})

	for row in game.board.board:
		row_data = []
		for cell in row:
			if cell is None:
				row_data.append(None)
			else:
				row_data.append(cell.name)
		status["board"].append(row_data)

	return status


if __name__ == "__main__":
	uvicorn.run("__main__:app", host="0.0.0.0", port=80)
