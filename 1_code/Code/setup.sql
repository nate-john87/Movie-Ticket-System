CREATE DATABASE movie_ticket_db;

CREATE USER 'movieapp'@'localhost' IDENTIFIED BY 'MovieAppPass123!';
GRANT ALL PRIVILEGES ON movie_ticket_db.* TO 'movieapp'@'localhost';
FLUSH PRIVILEGES;

USE movie_ticket_db;
SELECT DATABASE();