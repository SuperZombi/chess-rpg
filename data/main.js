function setCookie(name, value, options = {}) {
	let age_time = Math.floor(new Date().getTime() / 1000) + (365 * 24 * 60 * 60);
	options = {path: '/', 'max-age': age_time, ...options};
	let updatedCookie = name + "=" + value;
	for (let optionKey in options) {
		updatedCookie += "; " + optionKey;
		let optionValue = options[optionKey];
		updatedCookie += "=" + optionValue;
	}
	document.cookie = updatedCookie;
}
function deleteCookie(name){
	setCookie(name, "", {'max-age': -1})
}
function getCookie(name) {
	let cookie = {};
	document.cookie.split(';').forEach(function(el) {
		let [k,v] = el.split('=');
		cookie[k.trim()] = v;
	})
	return cookie[name];
}


function get_cell(cords) {
	let [x, y] = cords;
	return document.querySelector(`.board .line:nth-child(${x+1}) .cell:nth-child(${y+1})`)
}
function get_all_cells(){
	return document.querySelectorAll(`.board .line .cell`)
}
function get_cell_cords(cell){
	let y = [...cell.parentElement.querySelectorAll(".cell")].indexOf(cell)
	let x = [...cell.parentElement.parentElement.querySelectorAll(".line")].indexOf(cell.parentElement)
	return [x, y]
}
function clear_board(){
	document.querySelectorAll(`.board .line .cell > .hero`).forEach(e=>{
		e.remove()
	})
	get_all_cells().forEach(cell=>{
		cell.classList.add("invisible")
	})
}
function addHero(cell, hero){
	cell.innerHTML = `
		<div class="hero ${hero.enemy ? "enemy" : ""}">
			<meter value="${hero.hp}" min="0" max="${hero.max_hp}" low="${hero.max_hp * 0.35}" optimum="${hero.max_hp}" high="${hero.max_hp * 0.75}"></meter>
			<i style="background-image: url(${hero.icon})"></i>
			<div class="about">
				<h3 style="margin:0; text-align: center;">${hero.name}</h3>
				<hr>
				<div>Здоровье: ${hero.hp}</div>
				<div>Атака: ${hero.attack}</div>
			</div>
		</div>`
}
function place_board(heroes, board, enemies){
	heroes.forEach(hero=>{
		let cell = get_cell(hero.position)
		addHero(cell, hero)
		init_move(cell, hero)
	})
	enemies.forEach(hero=>{
		let cell = get_cell(hero.position)
		hero.enemy = true;
		addHero(cell, hero)
	})
	board.forEach(e=>{
		let cell = get_cell(e)
		cell.classList.remove("invisible")
	})
}

function get_avalible_cells(cell, radius){
	let [x, y] = get_cell_cords(cell)
	let visible_cells = []
	for (let dx = -radius; dx <= radius; dx++) {
		for (let dy = -radius; dy <= radius; dy++) {
			if (dx == 0 && dy == 0){
				continue
			}
			if (Math.abs(dx) + Math.abs(dy) <= radius) {
				if (8 > x + dx  && x + dx >= 0 && 8 > y + dy && y + dy >= 0) {
					visible_cells.push([x + dx, y + dy]);
				}
			}
		}
	}
	return visible_cells
}
function clear_select(){
	document.querySelectorAll(`.board .line .cell.selected`).forEach(e=>{
		e.classList.remove("selected")
	})
	document.querySelectorAll(`.board .line .cell.avalible`).forEach(e=>{
		e.onclick = ""
		e.classList.remove("avalible")
	})
}

function init_move(cell, hero){
	cell.onclick = _=>{
		if (cell.classList.contains("selected")){
			clear_select()
			return
		}
		clear_select()
		cell.classList.add("selected")
		let avalible = get_avalible_cells(cell, hero.movement_range)
		avalible.forEach(cords=>{
			let temp_cell = get_cell(cords)
			if (temp_cell.querySelector(".hero")){
				return
			}
			temp_cell.classList.add("avalible")
			temp_cell.onclick = _=>{
				move_hero(cell, temp_cell)
			}
		})
	}
}



var PLAYER_ID;
const socketURL = 'ws://' + document.domain + ':' + location.port;
window.onload = _=>{
	let userName = getCookie("userName")
	if (userName){
		let input = document.querySelector("#userName")
		input.value = userName
	}

	let button = document.querySelector("#search_game")
	button.onclick = search_game
	// function sendMessage(event) {   
	//     ws.send(input.value)
	// }
}

function search_game(){
	let input = document.querySelector("#userName")
	if (input.value.trim() != ""){
		setCookie("userName", input.value.trim())

		var ws = new WebSocket(socketURL + "/api/search_game");
		ws.onopen = function(event) {
			console.log("Поиск игры...");
			document.querySelector(".search_animation").style.display = "flex"
			document.querySelector("#search_game").innerHTML = "Выйти из очереди"
			document.querySelector("#search_game").onclick = _=>{
				ws.close();
				document.querySelector("#search_game").onclick = search_game;
			}
		};
		ws.onmessage = function(event) {
			console.log(event)
		};
		ws.onclose = function(event) {
			if (!event.wasClean){
				alert("Пользователь с таким именем уже существует")
			}
			document.querySelector(".search_animation").style.display = "none"
			document.querySelector("#search_game").innerHTML = "Search Game"
		};
	}
}


function start_game(){
	let xhr = new XMLHttpRequest();
	xhr.open("POST", `/api/new_game`)
	// xhr.setRequestHeader('Content-type', 'application/json; charset=utf-8');
	xhr.onload = function() {
		document.querySelector(".board-wrapper").style.opacity = "1"
		
		if (xhr.status == 200){
			let answer = JSON.parse(xhr.response);
			console.log(answer)
			PLAYER_ID = answer.your_player_id;
			if (answer.your_player_id == 1){
				document.querySelector(".board").classList.add("rotate")
			}
			clear_board()
			place_board(answer.heroes, answer.board, [])
		}
	}
	xhr.send()
	// xhr.send(JSON.stringify({
	// 	'user': local_storage.userName
	// }))
}

function move_hero(cell, new_cell){
	clear_select()

	let xhr = new XMLHttpRequest();
	xhr.open("POST", `/api/move_hero`)
	xhr.setRequestHeader('Content-type', 'application/json; charset=utf-8');
	xhr.onload = function() {
		if (xhr.status == 200){
			let answer = JSON.parse(xhr.response);
			console.log(answer)
			if (answer.success){
				clear_board()
				place_board(answer.heroes, answer.board, answer.enemies)
			}
			else{
				alert("Не ваш ход")
			}
		}
	}
	xhr.send(JSON.stringify({
		'player_id': PLAYER_ID,
		"old_cords": get_cell_cords(cell),
		"new_cords": get_cell_cords(new_cell)
	}))
}
