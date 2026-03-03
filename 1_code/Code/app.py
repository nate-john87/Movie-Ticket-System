from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_conn

app = Flask(__name__)
app.secret_key = "dev-secret"


@app.get("/")
def home():
    return redirect(url_for("movies"))


@app.get("/movies")
def movies():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, title, rating, runtime_minutes FROM movies ORDER BY id;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("movies.html", movies=rows)


@app.get("/movies/<int:movie_id>/showtimes")
def showtimes(movie_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM movies WHERE id=%s;", (movie_id,))
    movie = cur.fetchone()

    cur.execute("""
        SELECT id, start_time, base_price
        FROM showtimes
        WHERE movie_id=%s
        ORDER BY start_time;
    """, (movie_id,))
    times = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("showtimes.html", movie=movie, showtimes=times)


@app.get("/showtimes/<int:showtime_id>/seats")
def seats(showtime_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT s.id as showtime_id, s.start_time, s.base_price, m.title
        FROM showtimes s
        JOIN movies m ON m.id=s.movie_id
        WHERE s.id=%s;
    """, (showtime_id,))
    info = cur.fetchone()

    cur.execute("""
        SELECT seat.id, seat.row_label, seat.seat_number, ss.status
        FROM showtime_seats ss
        JOIN seats seat ON seat.id=ss.seat_id
        WHERE ss.showtime_id=%s
        ORDER BY seat.row_label, seat.seat_number;
    """, (showtime_id,))
    seat_rows = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("seats.html", info=info, seats=seat_rows)


@app.post("/showtimes/<int:showtime_id>/purchase")
def purchase(showtime_id):
    customer_name = request.form.get("customer_name", "").strip()
    selected_seats = request.form.getlist("seat_id")

    if not customer_name:
        flash("Please enter your name.")
        return redirect(url_for("seats", showtime_id=showtime_id))

    if not selected_seats:
        flash("Please select at least one seat.")
        return redirect(url_for("seats", showtime_id=showtime_id))

    seat_ids = [int(x) for x in selected_seats]

    conn = get_conn()
    try:
        conn.start_transaction()
        cur = conn.cursor(dictionary=True)

        format_strings = ",".join(["%s"] * len(seat_ids))
        cur.execute(f"""
            SELECT seat_id, status
            FROM showtime_seats
            WHERE showtime_id=%s AND seat_id IN ({format_strings})
            FOR UPDATE;
        """, (showtime_id, *seat_ids))
        statuses = cur.fetchall()

        if len(statuses) != len(seat_ids) or any(r["status"] != "AVAILABLE" for r in statuses):
            conn.rollback()
            flash("One or more selected seats are no longer available.")
            return redirect(url_for("seats", showtime_id=showtime_id))

        cur.execute(
            "INSERT INTO bookings (showtime_id, customer_name) VALUES (%s, %s);",
            (showtime_id, customer_name),
        )
        booking_id = cur.lastrowid

        for seat_id in seat_ids:
            cur.execute(
                "INSERT INTO booking_seats (booking_id, seat_id) VALUES (%s, %s);",
                (booking_id, seat_id),
            )

        cur.execute(f"""
            UPDATE showtime_seats
            SET status='SOLD'
            WHERE showtime_id=%s AND seat_id IN ({format_strings});
        """, (showtime_id, *seat_ids))

        conn.commit()
        return redirect(url_for("confirmation", booking_id=booking_id))

    finally:
        conn.close()


@app.get("/confirmation/<int:booking_id>")
def confirmation(booking_id):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT b.id, b.customer_name, b.created_at, m.title, s.start_time, s.base_price
        FROM bookings b
        JOIN showtimes s ON s.id=b.showtime_id
        JOIN movies m ON m.id=s.movie_id
        WHERE b.id=%s;
    """, (booking_id,))
    booking = cur.fetchone()

    cur.execute("""
        SELECT seat.row_label, seat.seat_number
        FROM booking_seats bs
        JOIN seats seat ON seat.id=bs.seat_id
        WHERE bs.booking_id=%s
        ORDER BY seat.row_label, seat.seat_number;
    """, (booking_id,))
    seats = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("confirmation.html", booking=booking, seats=seats)


@app.get("/admin/showtimes/add")
def admin_add_showtime_form():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, title FROM movies ORDER BY id;")
    movies = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin_add_showtime.html", movies=movies)


@app.post("/admin/showtimes/add")
def admin_add_showtime_submit():
    movie_id = request.form.get("movie_id")
    start_time = request.form.get("start_time")  
    base_price = request.form.get("base_price")

    if not (movie_id and start_time and base_price):
        flash("Please fill out all fields.")
        return redirect(url_for("admin_add_showtime_form"))

    start_time_sql = start_time.replace("T", " ") + ":00"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO showtimes (movie_id, start_time, base_price) VALUES (%s, %s, %s);",
        (movie_id, start_time_sql, base_price),
    )
    showtime_id = cur.lastrowid

    cur.execute("""
        INSERT INTO showtime_seats (showtime_id, seat_id, status)
        SELECT %s, id, 'AVAILABLE' FROM seats;
    """, (showtime_id,))
    conn.commit()

    cur.close()
    conn.close()

    flash("Showtime added successfully.")
    return redirect(url_for("movies"))

@app.get("/favicon.ico")
def favicon():
    return "", 204

@app.get("/admin/movies/add")
def admin_add_movie_form():
    return render_template("admin_add_movie.html")


@app.post("/admin/movies/add")
def admin_add_movie_submit():
    title = request.form.get("title", "").strip()
    rating = request.form.get("rating", "").strip()
    runtime_minutes = request.form.get("runtime_minutes", "").strip()

    if not title:
        flash("Title is required.")
        return redirect(url_for("admin_add_movie_form"))

    runtime_val = None
    if runtime_minutes:
        try:
            runtime_val = int(runtime_minutes)
            if runtime_val <= 0:
                flash("Runtime must be a positive number.")
                return redirect(url_for("admin_add_movie_form"))
        except ValueError:
            flash("Runtime must be a whole number (minutes).")
            return redirect(url_for("admin_add_movie_form"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO movies (title, rating, runtime_minutes) VALUES (%s, %s, %s);",
        (title, rating if rating else None, runtime_val),
    )
    conn.commit()
    cur.close()
    conn.close()

    flash("Movie added successfully.")
    return redirect(url_for("movies"))

@app.get("/admin/bookings")
def admin_view_bookings():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    # Main booking info
    cur.execute("""
        SELECT b.id, b.customer_name, b.created_at, b.status,
               m.title, s.start_time
        FROM bookings b
        JOIN showtimes s ON s.id = b.showtime_id
        JOIN movies m ON m.id = s.movie_id
        ORDER BY b.created_at DESC;
    """)
    bookings = cur.fetchall()

    # Fetch seats for each booking
    for booking in bookings:
        cur.execute("""
            SELECT seat.row_label, seat.seat_number
            FROM booking_seats bs
            JOIN seats seat ON seat.id = bs.seat_id
            WHERE bs.booking_id = %s
            ORDER BY seat.row_label, seat.seat_number;
        """, (booking["id"],))
        seats = cur.fetchall()
        booking["seats"] = seats

    cur.close()
    conn.close()

    return render_template("admin_bookings.html", bookings=bookings)

@app.post("/admin/bookings/<int:booking_id>/cancel")
def admin_cancel_booking(booking_id):
    conn = get_conn()
    try:
        conn.start_transaction()
        cur = conn.cursor(dictionary=True)

        # Lock the booking row
        cur.execute("""
            SELECT id, showtime_id, status
            FROM bookings
            WHERE id=%s
            FOR UPDATE;
        """, (booking_id,))
        booking = cur.fetchone()

        if not booking:
            conn.rollback()
            flash("Booking not found.")
            return redirect(url_for("admin_view_bookings"))

        if booking["status"] == "CANCELLED":
            conn.rollback()
            flash("Booking is already cancelled.")
            return redirect(url_for("admin_view_bookings"))

        # Get seats for this booking
        cur.execute("""
            SELECT seat_id
            FROM booking_seats
            WHERE booking_id=%s;
        """, (booking_id,))
        seat_ids = [row["seat_id"] for row in cur.fetchall()]

        if seat_ids:
            placeholders = ",".join(["%s"] * len(seat_ids))

            # Release seats back to AVAILABLE for this showtime
            cur.execute(f"""
                UPDATE showtime_seats
                SET status='AVAILABLE'
                WHERE showtime_id=%s AND seat_id IN ({placeholders});
            """, (booking["showtime_id"], *seat_ids))

        # Mark booking cancelled (keep history)
        cur.execute("""
            UPDATE bookings
            SET status='CANCELLED'
            WHERE id=%s;
        """, (booking_id,))

        conn.commit()
        flash(f"Booking {booking_id} cancelled and seats released.")
        return redirect(url_for("admin_view_bookings"))

    except Exception as e:
        conn.rollback()
        flash(f"Error cancelling booking: {e}")
        return redirect(url_for("admin_view_bookings"))
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)