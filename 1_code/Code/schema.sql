USE movie_ticket_db;

DROP TABLE IF EXISTS booking_seats;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS showtime_seats;
DROP TABLE IF EXISTS seats;
DROP TABLE IF EXISTS showtimes;
DROP TABLE IF EXISTS movies;

CREATE TABLE movies (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  rating VARCHAR(10),
  runtime_minutes INT
);

CREATE TABLE showtimes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  movie_id INT NOT NULL,
  start_time DATETIME NOT NULL,
  base_price DECIMAL(6,2) NOT NULL,
  FOREIGN KEY (movie_id) REFERENCES movies(id)
);

CREATE TABLE seats (
  id INT AUTO_INCREMENT PRIMARY KEY,
  row_label CHAR(1) NOT NULL,
  seat_number INT NOT NULL
);

CREATE TABLE showtime_seats (
  showtime_id INT NOT NULL,
  seat_id INT NOT NULL,
  status ENUM('AVAILABLE','SOLD') NOT NULL DEFAULT 'AVAILABLE',
  PRIMARY KEY (showtime_id, seat_id),
  FOREIGN KEY (showtime_id) REFERENCES showtimes(id),
  FOREIGN KEY (seat_id) REFERENCES seats(id)
);

CREATE TABLE bookings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  showtime_id INT NOT NULL,
  customer_name VARCHAR(200) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('CONFIRMED','CANCELLED') NOT NULL DEFAULT 'CONFIRMED',
  FOREIGN KEY (showtime_id) REFERENCES showtimes(id)
);

CREATE TABLE booking_seats (
  booking_id INT NOT NULL,
  seat_id INT NOT NULL,
  PRIMARY KEY (booking_id, seat_id),
  FOREIGN KEY (booking_id) REFERENCES bookings(id),
  FOREIGN KEY (seat_id) REFERENCES seats(id)
);

SHOW TABLES;