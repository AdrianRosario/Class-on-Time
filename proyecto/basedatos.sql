
tabla del backend
create table tareas(
 idcreador integer,
 nombe_tareas varchar(200),
 descripcion varchar(300)
 idtares integer,
 tipos varchar(200),
 PRIMARY KEY (idtares)
)

--  tabla de login
create table prueba(
	id integer,
	nombre varchar(200),
	email varchar(200),
	password varchar(200),
	token varchar(200),
	PRIMARY KEY (id)

)