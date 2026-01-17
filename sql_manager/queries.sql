create table ability(
		id_ability serial primary key,
		name varchar(30),
		url varchar(50),
		url_id int
)

create table pokes(
		id_pokes int primary key,
		base_experience int,
		height int,
		name varchar(30),
		poke_order int,
		weight int
)



create table pokes_ability(
		id_ability INT,
		id_pokes INT,
		PRIMARY KEY (id_ability, id_pokes),
		FOREIGN KEY (id_ability) REFERENCES ability(id_ability),
		FOREIGN KEY (id_pokes) REFERENCES pokes(id_pokes)




create table poke_media(
        id serial primary key,
        name varchar(50),
        media_url varchar(200)
)