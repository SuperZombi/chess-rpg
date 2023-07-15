from heroes import *
from game import *

import os
import time
import hashlib
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi import Request
import uvicorn
from pydantic import BaseModel
from fastapi.websockets import WebSocket, WebSocketDisconnect

app = FastAPI()

@app.get("/", response_class=FileResponse)
def home():
	return FileResponse("data/index.html")

ALL_HEROES = [Ninja(), Damager(), Tank(), Wizard()]

@app.get("/api/get_heroes")
async def get_heroes():
	return ALL_HEROES


GAMES_QUEUE = {}
ActiveGames = {}
USERS = {}

def heroes_as_dict(arr):
	def serialize(cls):
		return cls.__dict__
	return json.loads(json.dumps(arr, default=serialize))

@app.websocket("/api/search_game")
async def search_game(websocket: WebSocket, data: str):
	await websocket.accept()
	user_name = websocket.cookies.get("userName")
	data = json.loads(data)
	if not 'heroes' in data.keys():
		await websocket.close(reason="heroes_not_specified")
		return
	if user_name and not user_name in GAMES_QUEUE.keys():
		user_heroes = [hero.new() for hero in ALL_HEROES if hero.name in data['heroes']]
		if len(GAMES_QUEUE.keys()) > 0:
			opponent = list(GAMES_QUEUE.keys())[0]
			op_soc = GAMES_QUEUE[opponent]["socket"]
			op_heroes = GAMES_QUEUE[opponent]["heroes"]
			del GAMES_QUEUE[opponent]

			game_id, game = new_game({"name": opponent, "socket": op_soc, "heroes": op_heroes},
							{"name": user_name, "socket": websocket, "heroes": user_heroes})

			player1_heroes = heroes_as_dict(game.get_player_heroes(opponent))
			visible1 = game.get_visible_cells(opponent)

			player2_heroes = heroes_as_dict(game.get_player_heroes(user_name))
			visible2 = game.get_visible_cells(user_name)

			await op_soc.send_json({
				"player_id": 1,
				"opponent_name": user_name, "game_founded": True, "game_id": game_id,
				"now_turn": game.current_player, "heroes": player1_heroes, "board": visible1
			})
			await websocket.send_json({
				"player_id": 2,
				"opponent_name": opponent, "game_founded": True, "game_id": game_id,
				"now_turn": game.current_player, "heroes": player2_heroes, "board": visible2
			})
		else:
			GAMES_QUEUE[user_name] = {"socket": websocket, "heroes": user_heroes}
		print(GAMES_QUEUE)
		try:
			while True:
				await websocket.receive_text()
		except WebSocketDisconnect as e:
			if user_name in GAMES_QUEUE.keys():
				del GAMES_QUEUE[user_name]
				print(GAMES_QUEUE)

			usr = USERS.get(user_name)
			if usr and usr.get("in_game"):
				game = ActiveGames[usr.get("in_game")]
				op = game.get_opponent(user_name)
				await op.socket.send_json({
					"finish_game": True,
					"reason": "opponent_disconnect",
					"winer": op.name
				})
				del ActiveGames[usr.get("in_game")]
				del USERS[user_name]
				usr2 = USERS.get(op.name)
				if usr2 and usr2.get("in_game"):
					del USERS[op.name]
	else:
		await websocket.close(reason="user_already_exists")

def new_game(player1, player2):
	player1 = Player(player1["name"], player1["socket"], player1["heroes"])
	player2 = Player(player2["name"], player2["socket"], player2["heroes"])

	game = Game(player1, player2)
	game.board.print_board()

	game_id = hashlib.md5(str(time.time()).encode()).hexdigest()
	ActiveGames[game_id] = game

	USERS[player1.name] = {"in_game": game_id}
	USERS[player2.name] = {"in_game": game_id}

	return game_id, game

class move_hero_model(BaseModel):
	game_id: str
	player_id: str
	old_cords: list
	new_cords: list
	talant: str = None

@app.post("/api/move_hero")
async def move_hero(args: move_hero_model):
	game = ActiveGames[args.game_id]
	if game.current_player == args.player_id:
		hero = game.get_hero_by_cords(args.player_id, args.old_cords)
		if hero:
			if game.move_hero(args.player_id, hero, args.new_cords):
				game.board.print_board()
				winer = game.switch_player()

				player_heroes = game.get_player_heroes(args.player_id)
				visible = game.get_visible_cells(args.player_id)
				enemies = game.get_visible_enemies(args.player_id, visible)

				player2_heroes = game.get_enemy_heroes(args.player_id)
				visible2 = game.get_visible_cells(game.get_opponent(args.player_id).name)
				enemies2 = game.get_visible_enemies(game.get_opponent(args.player_id).name, visible2)

				op = game.get_opponent(args.player_id)
				await op.socket.send_json({
					"update_game": True,
					"now_turn": game.current_player, "heroes": heroes_as_dict(player2_heroes),
					"enemies": heroes_as_dict(enemies2), "board": visible2
				})

				answer = {"success": True, "now_turn": game.current_player, "heroes": heroes_as_dict(player_heroes),
						"enemies": heroes_as_dict(enemies), "board": visible}
				if winer:
					answer['winer'] = winer.name
					answer["finish_game"] = True
					await op.socket.send_json({
						"finish_game": True,
						"winer": winer.name
					})
					del ActiveGames[args.game_id]
					for usr in [args.player_id, op.name]:
						x = USERS.get(usr)
						if x and x.get("in_game"):
							del USERS[usr]
				return answer
	return {"success": False}


@app.post("/api/atack_hero")
async def attack_hero(args: move_hero_model):
	game = ActiveGames[args.game_id]
	if game.current_player == args.player_id:
		hero = game.get_hero_by_cords(args.player_id, args.old_cords)
		if hero:
			if args.talant:
				if not game.use_talant(args.player_id, hero, args.talant, args.new_cords):
					return {"success": False}
			else:
				if not game.attack_hero(args.player_id, hero, args.new_cords):
					return {"success": False}
					
			game.board.print_board()
			winer = game.switch_player()

			player_heroes = game.get_player_heroes(args.player_id)
			visible = game.get_visible_cells(args.player_id)
			enemies = game.get_visible_enemies(args.player_id, visible)

			player2_heroes = game.get_enemy_heroes(args.player_id)
			visible2 = game.get_visible_cells(game.get_opponent(args.player_id).name)
			enemies2 = game.get_visible_enemies(game.get_opponent(args.player_id).name, visible2)

			op = game.get_opponent(args.player_id)
			await op.socket.send_json({
				"update_game": True,
				"now_turn": game.current_player, "heroes": heroes_as_dict(player2_heroes),
				"enemies": heroes_as_dict(enemies2), "board": visible2
			})
			answer = {"success": True, "now_turn": game.current_player, "heroes": heroes_as_dict(player_heroes),
					"enemies": heroes_as_dict(enemies), "board": visible}
			if winer:
				answer['winer'] = winer.name
				answer["finish_game"] = True
				await op.socket.send_json({
					"finish_game": True,
					"winer": winer.name
				})
				del ActiveGames[args.game_id]
				for usr in [args.player_id, op.name]:
					x = USERS.get(usr)
					if x and x.get("in_game"):
						del USERS[usr]
			return answer
	return {"success": False}


@app.get("/{_:path}")
async def data(request: Request):
	path = request.url.path[1:]
	filepath = os.path.join("data", path)
	if os.path.exists(filepath):
		return FileResponse(filepath)
	raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
	uvicorn.run("__main__:app", host="0.0.0.0", port=80)
