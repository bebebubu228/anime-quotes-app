create database if not exists animequotes_db;

use animequotes_db;

create table users(
id int auto_increment primary key,
username varchar(30) unique not null,
email varchar(40) unique not null,
password_hash varchar(255) not null,
created_at timestamp default current_timestamp
);

create table quotes(
id int auto_increment primary key,
quote text not null,
anime_title varchar(255) not null,
name_character varchar(255) not null
);

create table favorite(
users_id int not null,
quotes_id int not null,
primary key (users_id, quotes_id),
foreign key (users_id) references users (id),
foreign key (quotes_id) references quotes (id)
);
