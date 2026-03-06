USE movie_ticket_db;

INSERT INTO movies (title, rating, runtime_minutes) VALUES
('Dune: Part Two', 'PG-13', 166),
('Inside Out 2', 'PG', 96);

INSERT INTO seats (row_label, seat_number) VALUES
('A',1),('A',2),('A',3),('A',4),('A',5),('A',6),('A',7),('A',8),
('B',1),('B',2),('B',3),('B',4),('B',5),('B',6),('B',7),('B',8),
('C',1),('C',2),('C',3),('C',4),('C',5),('C',6),('C',7),('C',8);

INSERT INTO showtimes (movie_id, start_time, base_price) VALUES
(1, '2026-03-05 19:00:00', 12.00),
(1, '2026-03-05 21:30:00', 12.00),
(2, '2026-03-05 18:15:00', 10.00);

INSERT INTO showtime_seats (showtime_id, seat_id, status)
SELECT s.id, seat.id, 'AVAILABLE'
FROM showtimes s
CROSS JOIN seats seat;