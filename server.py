from heroes import *
from game import *

import os
import time
import hashlib
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

@app.get("/{_:path}")
async def data(request: Request):
	path = request.url.path[1:]
	filepath = os.path.join("data", path)
	if os.path.exists(filepath):
		return FileResponse(filepath)
	raise HTTPException(status_code=404, detail="File not found")

GAMES_QUEUE = {}
ActiveGames = {}

def heroes_as_dict(arr):
	return list(map(lambda x: x.__dict__, arr))

@app.websocket("/api/search_game")
async def search_game(websocket: WebSocket):
	user_name = websocket.cookies.get("userName")
	if user_name and not user_name in GAMES_QUEUE.keys():
		await websocket.accept()
		if len(GAMES_QUEUE.keys()) > 0:
			opponent = list(GAMES_QUEUE.keys())[0]
			op_soc = GAMES_QUEUE[opponent]
			del GAMES_QUEUE[opponent]

			game_id, game = new_game({"name": opponent, "socket": op_soc},
							{"name": user_name, "socket": websocket})

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
			GAMES_QUEUE[user_name] = websocket
		print(GAMES_QUEUE)
		try:
			while True:
				await websocket.receive_text()
		except WebSocketDisconnect as e:
			if user_name in GAMES_QUEUE.keys():
				del GAMES_QUEUE[user_name]
				print(GAMES_QUEUE)
	else:
		await websocket.close()

def new_game(player1, player2):
	player1 = Player(player1["name"], player1["socket"], [Ninja(), Damager(), Tank()])
	player2 = Player(player2["name"], player2["socket"], [Ninja(), Damager(), Tank()])

	game = Game(player1, player2)
	game.board.print_board()

	game_id = hashlib.md5(str(time.time()).encode()).hexdigest()
	ActiveGames[game_id] = game

	return game_id, game

class move_hero_model(BaseModel):
	game_id: str
	player_id: str
	old_cords: list
	new_cords: list

@app.post("/api/move_hero")
async def move_hero(args: move_hero_model):
	game = ActiveGames[args.game_id]
	if game.current_player == args.player_id:
		hero = game.get_hero_by_cords(args.player_id, args.old_cords)
		if hero:
			if game.move_hero(args.player_id, hero, args.new_cords):
				game.board.print_board()
				game.switch_player()

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
				return {"success": True, "now_turn": game.current_player, "heroes": heroes_as_dict(player_heroes),
						"enemies": heroes_as_dict(enemies), "board": visible}
	return {"success": False}


@app.post("/api/atack_hero")
async def attack_hero(args: move_hero_model):
	game = ActiveGames[args.game_id]
	if game.current_player == args.player_id:
		hero = game.get_hero_by_cords(args.player_id, args.old_cords)
		if hero:
			if game.attack_hero(args.player_id, hero, args.new_cords):
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
				return answer
	return {"success": False}


if __name__ == "__main__":
	uvicorn.run("__main__:app", host="0.0.0.0", port=80)
