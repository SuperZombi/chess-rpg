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
			${hero.mana_max ? `<meter class="mana" value="${hero.mana_current}" min="0" max="${hero.mana_max}"></meter>` : ""}
			<i style="background-image: url(${hero.icon})"></i>
			<div class="about">
				<h3 style="margin:0; text-align: center;">${hero.name}</h3>
				<hr>
				<table>
					<tr><td>Здоровье:</td><td>${hero.hp}</td></tr>
					${hero.mana_max ? `<tr><td>Мана:</td><td>${hero.mana_current}</td></tr>` : ""}
					<tr><td>Атака:</td><td>${hero.attack}</td></tr>
				</table>
			</div>
			<div class="effects"></div>
		</div>`
	if (hero.effects.length > 0){
		cell.querySelector(".about").innerHTML += "<hr>"
		hero.effects.forEach(effect=>{
			cell.querySelector(".effects").innerHTML += `<span><img src="${effect.icon}"></span>`
			cell.querySelector(".about").innerHTML += `
			<fieldset>
				<legend>${effect.name}</legend>
				<table>
					${effect.damage ? `<tr><td>Урон:</td><td>${effect.damage}</td></tr>` : ""}
					${effect.hp ? `<tr><td>Лечение:</td><td>${effect.hp}</td></tr>` : ""}
					${effect.repeats ? `<tr><td>Повторов:</td><td>${effect.repeats}</td></tr>` : ""}
				</table>
			</fieldset>`
		})
	}
}
function place_board(heroes, board, enemies){
	heroes.forEach(hero=>{
		if (hero.alive){
			let cell = get_cell(hero.position)
			addHero(cell, hero)
			init_move(cell, hero)
		}
	})
	enemies.forEach(hero=>{
		if (hero.alive){
			let cell = get_cell(hero.position)
			hero.enemy = true;
			addHero(cell, hero)
		}
	})
	board.forEach(e=>{
		let cell = get_cell(e)
		cell.classList.remove("invisible")
	})
}

function get_avalible_cells(cell, visibility) {
	let [x, y] = get_cell_cords(cell)
	let visibleCells = []
    if (visibility % 2 === 0 || visibility > 4) {
        // Круглая видимость
        for (let dx = -visibility; dx <= visibility; dx++) {
            for (let dy = -visibility; dy <= visibility; dy++) {
                if (Math.abs(dx) + Math.abs(dy) <= visibility) {
                    if (x + dx >= 0 && x + dx < 8 && y + dy >= 0 && y + dy < 8) {
                        if (visibility > 2) {
                            if (
                                !(dx === -visibility && dy === 0) &&
                                !(dx === visibility && dy === 0) &&
                                !(dx === 0 && dy === -visibility) &&
                                !(dx === 0 && dy === visibility)
                            ) {
                                visibleCells.push([x + dx, y + dy]);
                            } else {
                                continue;
                            }
                        } else {
                            visibleCells.push([x + dx, y + dy]);
                        }
                    }
                }
            }
        }
    } else {
        visibility = Math.max(1, visibility - 1);
        // Квадратная видимость
        for (let dx = -visibility; dx <= visibility; dx++) {
            for (let dy = -visibility; dy <= visibility; dy++) {
                if (x + dx >= 0 && x + dx < 8 && y + dy >= 0 && y + dy < 8) {
                    if (visibility > 1) {
                        if (
                            !(dx === -visibility && dy === -visibility) &&
                            !(dx === -visibility && dy === visibility) &&
                            !(dx === visibility && dy === -visibility) &&
                            !(dx === visibility && dy === visibility)
                        ) {
                            visibleCells.push([x + dx, y + dy]);
                        } else {
                            continue;
                        }
                    } else {
                        visibleCells.push([x + dx, y + dy]);
                    }
                }
            }
        }
    }
    return visibleCells;
}

function clear_select(){
	document.querySelectorAll(`.board .line .cell.selected`).forEach(e=>{
		e.classList.remove("selected")
	})
	document.querySelectorAll(`.board .line .cell.avalible`).forEach(e=>{
		e.onclick = ""
		e.classList.remove("avalible")
	})
	document.querySelectorAll(`.board .line .cell.atack-avalible`).forEach(e=>{
		e.onclick = ""
		e.classList.remove("atack-avalible")
	})
	document.querySelector("#talantes").innerHTML = ""
}

function init_move(cell, hero){
	cell.onclick = _=>{
		if (cell.classList.contains("selected")){
			clear_select()
			return
		}
		clear_select()
		cell.classList.add("selected")

		let default_atack = document.createElement("label")
		default_atack.className = "talant"
		default_atack.innerHTML = `
			<input type="radio" name="talant" checked>
			<img src="images/sword.svg">
			<div class="description">
				<table>
					<tr><td>Урон:</td><td>${hero.attack}</td></tr>
				</table>
			</div>
		`
		default_atack.onclick =_=>{
			recalculate_atack_distance(hero.attack_range)
		}
		document.querySelector("#talantes").appendChild(default_atack)

		if (hero.talantes){
			hero.talantes.forEach(talant=>{
				let el = document.createElement("label")
				el.className = "talant"
				el.innerHTML = `
					<input data-name="${talant.name}" type="radio" name="talant" ${hero.mana_current < talant.cost ? "disabled" : ""}>
					<img src="${talant.icon}">
					<div class="description">
						<h3 style="margin:0;text-align:center">${talant.name}</h3>
						<hr>
						<table>
							${talant.damage ? `<tr><td>Урон:</td><td>${talant.damage}</td></tr>` : ""}
							${talant.hp ? `<tr><td>Лечение:</td><td>${talant.hp}</td></tr>` : ""}
							${talant.cost ? `<tr><td>Мана:</td><td>${talant.cost}</td></tr>` : ""}
							${talant.repeats ? `<tr><td>Повторений:</td><td>${talant.repeats}</td></tr>` : ""}
						</table>
					</div>
				`
				el.onclick = _=>{
					recalculate_atack_distance(talant.attack_range, talant.friendly)
				}
				document.querySelector("#talantes").appendChild(el)
			})
		}

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

		function recalculate_atack_distance(radius, friendly=false){
			document.querySelectorAll(`.board .line .cell.atack-avalible`).forEach(e=>{
				e.onclick = ""
				e.classList.remove("atack-avalible")
			})

			let atack_available = get_avalible_cells(cell, radius)
			atack_available.forEach(cords=>{
				let temp_cell = get_cell(cords)
				if (temp_cell.classList.contains("selected")){return}
				let selector = ".hero.enemy"
				if (friendly){selector = ".hero:not(.enemy)"}
				if (temp_cell.querySelector(selector)){
					temp_cell.classList.add("atack-avalible")
					temp_cell.onclick = _=>{
						atack_hero(cell, temp_cell)
					}
				}
			})
		}
		recalculate_atack_distance(hero.attack_range)
	}
}


const socketURL = `ws${location.protocol == "https:" ? "s" : ""}://` + document.domain + ':' + location.port;
window.onload = _=>{
	let userName = getCookie("userName")
	if (userName){
		let input = document.querySelector("#userName")
		input.value = userName
	}

	let button = document.querySelector("#search_game")
	button.onclick = search_game

	initHeroCarosel()
}

function create_board(x, y){
	document.querySelector(".board").innerHTML = ""
	for (let dy = 0; dy < y; dy++) {
		let line = document.createElement("div")
		line.className = "line"
		for (let dx = 0; dx < x; dx++) {
			let cell = document.createElement("div")
			cell.className = "cell"
			line.appendChild(cell)
		}
		document.querySelector(".board").appendChild(line)
	}
}

function search_game(){
	let input = document.querySelector("#userName")
	if (input.value.trim() != ""){
		setCookie("userName", input.value.trim())

		var heroes = [...document.querySelectorAll('.heroes-carusel input[type="checkbox"]:checked')]
		heroes = heroes.map(e=>{return e.closest(".hero").getAttribute("data-name")})
		if (heroes.length != 3){
			alert("Выберите три героя!")
			return
		}

		localStorage.setItem("heroes", JSON.stringify(heroes))
		var data = {
			heroes: heroes
		};
		var queryString = "data=" + encodeURIComponent(JSON.stringify(data));

		var ws = new WebSocket(socketURL + "/api/search_game?" + queryString);
		ws.onopen = function(event) {
			document.querySelector(".search_animation").style.display = "flex"
			document.querySelector("#search_game").innerHTML = "Выйти из очереди"
			document.querySelector("#search_game").onclick = _=>{
				ws.close();
			}
		};
		ws.onmessage = function(event) {
			let data = JSON.parse(event.data)
			if (data.game_founded){
				document.querySelector(".search_animation").style.display = "none"
				document.querySelector(".nickname-area").style.display = "none"
				document.querySelector("#search_game").innerHTML = "Search Game"
				document.querySelector("#search_game").onclick = search_game;
				document.querySelector("#search_game").disabled = true;
				start_game(data)
			}
			else if (data.update_game){
				update_game(data)
			}
			else if(data.finish_game){
				if (data.reason == "opponent_disconnect"){
					console.error("Opponent disconnected")
				}
				console.warn(`Победил: ${data.winer}`)
				alert(`Победил: ${data.winer}`)
			}
			else{
				console.log(data)
			}
		};
		ws.onclose = function(event) {
			if (event.reason == "user_already_exists"){
				alert("Пользователь с таким именем уже существует")
			}
			document.querySelector(".search_animation").style.display = "none"
			document.querySelector("#search_game").innerHTML = "Search Game"
			document.querySelector("#search_game").onclick = search_game;
			document.querySelector("#search_game").disabled = false;
		};
	}
}

var GAME_ID;
function start_game(data){
	console.log(data)
	create_board(8, 8)
	document.querySelector(".board-wrapper").style.opacity = "1"
	document.querySelector(".heroes-carusel").style.display = "none"
	GAME_ID = data.game_id;

	let players = document.querySelectorAll("#players .player")
	players[0].querySelector("img").src = `https://ui-avatars.com/api/?name=${getCookie("userName")}&length=1&color=fff&background=random&bold=true&format=svg&size=512`
	players[0].querySelector("span").innerHTML = getCookie("userName")
	players[1].querySelector("img").src = `https://ui-avatars.com/api/?name=${data.opponent_name}&length=1&color=fff&background=random&bold=true&format=svg&size=512`
	players[1].querySelector("span").innerHTML = data.opponent_name
	document.querySelector("#players").classList.remove("hide")

	clear_board()
	place_board(data.heroes, data.board, [])

	if (data.player_id == 1){
		document.querySelector(".board").classList.add("rotate")
	}
	console.warn(`Ход игрока: ${data.now_turn}`)
	if (data.now_turn == getCookie("userName")){
		document.querySelector("#now-turn").className = "my"
		document.querySelector(".board-wrapper").classList.add("my-turn")
	} else{
		document.querySelector("#now-turn").className = "opponent"
		document.querySelector(".board-wrapper").classList.remove("my-turn")
	}
}

function update_game(data) {
	console.log(data)
	clear_board()
	place_board(data.heroes, data.board, data.enemies)
	console.warn(`Ход игрока: ${data.now_turn}`)
	if (data.now_turn == getCookie("userName")){
		document.querySelector("#now-turn").className = "my"
		document.querySelector(".board-wrapper").classList.add("my-turn")
	} else{
		document.querySelector("#now-turn").className = "opponent"
		document.querySelector(".board-wrapper").classList.remove("my-turn")
	}
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
				cell.onclick = ""
				clear_board()
				place_board(answer.heroes, answer.board, answer.enemies)
				console.warn(`Ход игрока: ${answer.now_turn}`)
				if (answer.now_turn == getCookie("userName")){
					document.querySelector("#now-turn").className = "my"
					document.querySelector(".board-wrapper").classList.add("my-turn")
				} else{
					document.querySelector("#now-turn").className = "opponent"
					document.querySelector(".board-wrapper").classList.remove("my-turn")
				}
			}
			else{
				alert("Не ваш ход")
			}
		}
	}
	xhr.send(JSON.stringify({
		'player_id': getCookie("userName"),
		'game_id': GAME_ID,
		"old_cords": get_cell_cords(cell),
		"new_cords": get_cell_cords(new_cell)
	}))
}

function atack_hero(cell, target_cell){
	let talant = document.querySelector("#talantes input:checked").getAttribute("data-name")
	clear_select()

	let xhr = new XMLHttpRequest();
	xhr.open("POST", `/api/atack_hero`)
	xhr.setRequestHeader('Content-type', 'application/json; charset=utf-8');
	xhr.onload = function() {
		if (xhr.status == 200){
			let answer = JSON.parse(xhr.response);
			console.log(answer)
			if (answer.success){
				clear_board()
				place_board(answer.heroes, answer.board, answer.enemies)

				if (answer.finish_game){
					console.warn(`Победил: ${answer.winer}`)
					alert(`Победил: ${answer.winer}`)
				} else{
					console.warn(`Ход игрока: ${answer.now_turn}`)
					if (answer.now_turn == getCookie("userName")){
						document.querySelector("#now-turn").className = "my"
						document.querySelector(".board-wrapper").classList.add("my-turn")
					} else{
						document.querySelector("#now-turn").className = "opponent"
						document.querySelector(".board-wrapper").classList.remove("my-turn")
					}
				}
			}
			else{
				alert("Не ваш ход")
			}
		}
	}
	let data = {
		'player_id': getCookie("userName"),
		'game_id': GAME_ID,
		"old_cords": get_cell_cords(cell),
		"new_cords": get_cell_cords(target_cell)
	}
	if (talant){
		data["talant"] = talant
	}
	xhr.send(JSON.stringify(data))
}


function addHeroToCarosel(hero){
	let carosel = document.querySelector(".heroes-carusel")
	let talants_area = ""
	hero.talantes ? hero.talantes.forEach(talant=>{
		talants_area += `
			<details>
				<summary>${talant.name}</summary>
				<table>
					${talant.damage ? `<tr><td>Урон:</td><td>${talant.damage}</td></tr>` : ""}
					${talant.hp ? `<tr><td>Лечение:</td><td>${talant.hp}</td></tr>` : ""}
					${talant.repeats ? `<tr><td>Повторов:</td><td>${talant.repeats}</td></tr>` : ""}
					${talant.cost ? `<tr><td>Мана:</td><td>${talant.cost}</td></tr>` : ""}
				</table>
			</details>
		`
	}) : ""
	
	carosel.innerHTML += `
		<div class="hero" data-name="${hero.name}">
			<label>
				<input type="checkbox" value="${hero.name}">
				<i style="background-image: url(${hero.icon});"></i>
			</label>
			
			<div class="description">
				<h3 style="margin:0; text-align: center;">${hero.name}</h3>
				<hr>
				<table>
					<tr><td>Здоровье:</td><td>${hero.hp}</td></tr>
					${hero.mana_max ? `<tr><td>Мана:</td><td>${hero.mana_max}</td></tr>` : ""}
					<tr><td>Атака:</td><td>${hero.attack}</td></tr>
					<tr><td>Обзор:</td><td>${hero.visibility}</td></tr>
				</table>
				${hero.talantes ? "<hr><div class='talants'>" + talants_area + "</div>": ""}
			</div>
		</div>
	`
}
function initHeroCarosel(){
	let xhr = new XMLHttpRequest();
	xhr.open("GET", `/api/get_heroes`)
	xhr.onload = function() {
		if (xhr.status == 200){
			let answer = JSON.parse(xhr.response);
			answer.forEach(hero=>{
				addHeroToCarosel(hero)
			})
			interact()
		}
	}
	xhr.send()

	function interact(){
		var checkboxes = document.querySelectorAll('.heroes-carusel input[type="checkbox"]');
		var maxLimit = 3;

		let heroes = JSON.parse(localStorage.getItem("heroes"))
		if (heroes){
			heroes.forEach(hero=>{
				let el = document.querySelector(`.heroes-carusel .hero[data-name='${hero}'] input[type="checkbox"]`);
				if (el){el.checked = true}
			})
		} else{
			let auto = [...checkboxes].slice(0, 3)
			auto.forEach(checkbox=>{checkbox.checked = true})
		}
		handleCheckboxChange()

		function handleCheckboxChange() {
			var checkedCount = 0;
			for (var i = 0; i < checkboxes.length; i++) {
				if (checkboxes[i].checked) {
					checkedCount++;
				}
			}
			for (var j = 0; j < checkboxes.length; j++) {
				if (checkedCount >= maxLimit && !checkboxes[j].checked) {
					checkboxes[j].disabled = true;
				} else {
					checkboxes[j].disabled = false;
				}
			}
		}

		for (var i = 0; i < checkboxes.length; i++) {
			checkboxes[i].addEventListener('click', handleCheckboxChange);
		}
	}
}