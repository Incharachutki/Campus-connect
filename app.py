from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import time
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = "campus_connect_secret_key"


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(
    BASE_DIR,
    "database.db"
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads"
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ============================================================
# CREATE UPLOAD FOLDER
# ============================================================

# exist_ok=True means:
# - create the folder if it does not exist
# - do nothing if it already exists
#
# This prevents FileExistsError on Windows.

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA busy_timeout = 10000"
    )

    return connection


# ============================================================
# IMAGE VALIDATION
# ============================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    connection = get_db_connection()

    try:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS events (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                description TEXT NOT NULL,

                date TEXT NOT NULL,

                venue TEXT NOT NULL

            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS registrations (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                student_name TEXT,

                usn TEXT,

                email TEXT,

                phone TEXT,

                department TEXT,

                year TEXT,

                event TEXT,

                registration_date TEXT

            )
            """
        )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# UPDATE EXISTING DATABASE STRUCTURE
# ============================================================

def fix_database():

    connection = get_db_connection()

    try:

        # ----------------------------------------------------
        # EVENTS TABLE
        # ----------------------------------------------------

        event_columns = connection.execute(
            "PRAGMA table_info(events)"
        ).fetchall()

        existing_event_columns = [
            column["name"]
            for column in event_columns
        ]

        required_event_columns = {

            "name": "TEXT",
            "description": "TEXT",
            "date": "TEXT",
            "venue": "TEXT",
            "image": "TEXT"

        }

        for column_name, column_type in required_event_columns.items():

            if column_name not in existing_event_columns:

                connection.execute(
                    f"""
                    ALTER TABLE events
                    ADD COLUMN {column_name} {column_type}
                    """
                )


        # ----------------------------------------------------
        # REGISTRATIONS TABLE
        # ----------------------------------------------------

        registration_columns = connection.execute(
            "PRAGMA table_info(registrations)"
        ).fetchall()

        existing_registration_columns = [
            column["name"]
            for column in registration_columns
        ]

        required_registration_columns = {

            "student_name": "TEXT",
            "usn": "TEXT",
            "email": "TEXT",
            "phone": "TEXT",
            "department": "TEXT",
            "year": "TEXT",
            "event": "TEXT",
            "registration_date": "TEXT"

        }

        for column_name, column_type in required_registration_columns.items():

            if column_name not in existing_registration_columns:

                connection.execute(
                    f"""
                    ALTER TABLE registrations
                    ADD COLUMN {column_name} {column_type}
                    """
                )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# DEFAULT EVENTS
# ============================================================

def add_default_events():

    connection = get_db_connection()

    try:

        result = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM events
            """
        ).fetchone()

        # Only add default events if the table is empty.

        if result["count"] == 0:

            event_columns = [
                column["name"]
                for column in connection.execute(
                    "PRAGMA table_info(events)"
                ).fetchall()
            ]

            default_events = [

                (
                    "Tech Fest 2026",
                    "A technical festival featuring coding, innovation and technology activities.",
                    "2026-10-15",
                    "Main Auditorium"
                ),

                (
                    "Hackathon 2026",
                    "Build innovative solutions to real-world problems in this campus hackathon.",
                    "2026-10-20",
                    "Innovation Lab"
                ),

                (
                    "Cultural Fest 2026",
                    "A celebration of music, dance, art and cultural activities.",
                    "2026-10-25",
                    "College Ground"
                ),

                (
                    "Sports Meet 2026",
                    "Annual college sports competition featuring multiple sporting events.",
                    "2026-11-05",
                    "Sports Ground"
                ),

                (
                    "AI Workshop",
                    "Hands-on workshop covering Artificial Intelligence and Machine Learning.",
                    "2026-11-10",
                    "Computer Lab"
                ),

                (
                    "Career Guidance Session",
                    "Career guidance and interaction session with industry professionals.",
                    "2026-11-15",
                    "Seminar Hall"
                )

            ]

            for event in default_events:

                name = event[0]
                description = event[1]
                date = event[2]
                venue = event[3]

                columns = []
                values = []

                if "name" in event_columns:

                    columns.append("name")
                    values.append(name)

                if "description" in event_columns:

                    columns.append("description")
                    values.append(description)

                if "date" in event_columns:

                    columns.append("date")
                    values.append(date)

                if "venue" in event_columns:

                    columns.append("venue")
                    values.append(venue)

                # Legacy columns

                if "category" in event_columns:

                    columns.append("category")
                    values.append("General")

                if "time" in event_columns:

                    columns.append("time")
                    values.append("TBD")

                if "location" in event_columns:

                    columns.append("location")
                    values.append(venue)

                if "emoji" in event_columns:

                    columns.append("emoji")
                    values.append("🎓")

                if "image" in event_columns:

                    columns.append("image")
                    values.append(None)

                placeholders = ", ".join(
                    ["?"] * len(columns)
                )

                column_string = ", ".join(
                    columns
                )

                connection.execute(
                    f"""
                    INSERT INTO events
                    ({column_string})
                    VALUES ({placeholders})
                    """,
                    values
                )

            connection.commit()

    finally:

        connection.close()


# ============================================================
# NO CACHE
# ============================================================

@app.after_request
def add_no_cache_headers(response):

    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    return response


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    connection = get_db_connection()

    try:

        events = connection.execute(
            """
            SELECT *
            FROM events
            ORDER BY date ASC
            """
        ).fetchall()

    finally:

        connection.close()

    return render_template(
        "index.html",
        events=events
    )


# ============================================================
# EVENTS
# ============================================================

@app.route("/events")
def events():

    connection = get_db_connection()

    try:

        events_list = connection.execute(
            """
            SELECT *
            FROM events
            ORDER BY date ASC
            """
        ).fetchall()

    finally:

        connection.close()

    return render_template(
        "events.html",
        events=events_list
    )


# ============================================================
# REGISTER PAGE
# ============================================================

@app.route("/register")
def register():

    connection = get_db_connection()

    try:

        events_list = connection.execute(
            """
            SELECT *
            FROM events
            ORDER BY date ASC
            """
        ).fetchall()

    finally:

        connection.close()

    return render_template(
        "register.html",
        events=events_list
    )


# ============================================================
# STUDENT REGISTRATION
# ============================================================

@app.route(
    "/submit-registration",
    methods=["POST"]
)
def submit_registration():

    student_name = request.form.get(
        "student_name",
        ""
    ).strip()

    usn = request.form.get(
        "usn",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    department = request.form.get(
        "department",
        ""
    ).strip()

    year = request.form.get(
        "year",
        ""
    ).strip()

    event = request.form.get(
        "event",
        ""
    ).strip()


    if not student_name:
        return "Student name is required."

    if not usn:
        return "USN is required."

    if not email:
        return "Email is required."

    if not phone:
        return "Phone number is required."

    if not department:
        return "Department is required."

    if not year:
        return "Year is required."

    if not event:
        return "Please select an event."


    connection = get_db_connection()

    try:

        connection.execute(
            """
            INSERT INTO registrations
            (
                student_name,
                usn,
                email,
                phone,
                department,
                year,
                event,
                registration_date
            )
            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                datetime('now', 'localtime')
            )
            """,
            (
                student_name,
                usn,
                email,
                phone,
                department,
                year,
                event
            )
        )

        connection.commit()

    except Exception as error:

        connection.rollback()

        return (
            "Registration failed: "
            + str(error)
        )

    finally:

        connection.close()


    # Get events again for the registration page.

    connection = get_db_connection()

    try:

        events_list = connection.execute(
            """
            SELECT *
            FROM events
            ORDER BY date ASC
            """
        ).fetchall()

    finally:

        connection.close()


    return render_template(
        "register.html",
        success=True,
        student_name=student_name,
        event=event,
        events=events_list
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()


        if (
            username == "admin"
            and
            password == "admin123"
        ):

            session["admin"] = True

            return redirect(
                url_for("admin")
            )


        return render_template(
            "login.html",
            error="Invalid username or password."
        )


    return render_template(
        "login.html"
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin")
def admin():

    if not session.get("admin"):

        return redirect(
            url_for("login")
        )


    connection = get_db_connection()

    try:

        registrations = connection.execute(
            """
            SELECT *
            FROM registrations
            ORDER BY id DESC
            """
        ).fetchall()


        events = connection.execute(
            """
            SELECT *
            FROM events
            ORDER BY date ASC
            """
        ).fetchall()

    finally:

        connection.close()


    return render_template(
        "admin.html",
        registrations=registrations,
        events=events
    )


# ============================================================
# ADD EVENT
# ============================================================

@app.route(
    "/admin/events/add",
    methods=["POST"]
)
def add_event():

    if not session.get("admin"):

        return redirect(
            url_for("login")
        )


    name = request.form.get(
        "name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    date = request.form.get(
        "date",
        ""
    ).strip()

    venue = request.form.get(
        "venue",
        ""
    ).strip()


    if not name:
        return "Event name is required."

    if not description:
        return "Event description is required."

    if not date:
        return "Event date is required."

    if not venue:
        return "Event venue is required."


    # --------------------------------------------------------
    # IMAGE UPLOAD
    # --------------------------------------------------------

    image = request.files.get(
        "event_image"
    )

    image_filename = None


    if image and image.filename:

        if not allowed_file(
            image.filename
        ):

            return (
                "Invalid image format. "
                "Please upload PNG, JPG, JPEG, GIF or WEBP."
            )


        original_filename = secure_filename(
            image.filename
        )


        filename_without_extension = os.path.splitext(
            original_filename
        )[0]

        extension = os.path.splitext(
            original_filename
        )[1].lower()


        # Add timestamp so two files with the same
        # name do not overwrite each other.

        image_filename = (
            filename_without_extension
            + "_"
            + str(int(time.time() * 1000))
            + extension
        )


        # Make absolutely sure the folder exists.

        os.makedirs(
            UPLOAD_FOLDER,
            exist_ok=True
        )


        image_path = os.path.join(
            UPLOAD_FOLDER,
            image_filename
        )


        image.save(
            image_path
        )


    # --------------------------------------------------------
    # DATABASE INSERT
    # --------------------------------------------------------

    connection = get_db_connection()

    try:

        table_info = connection.execute(
            "PRAGMA table_info(events)"
        ).fetchall()


        columns = [
            column["name"]
            for column in table_info
        ]


        # Make sure image column exists.

        if "image" not in columns:

            connection.execute(
                """
                ALTER TABLE events
                ADD COLUMN image TEXT
                """
            )

            columns.append("image")


        insert_columns = []
        insert_values = []


        # Main columns

        if "name" in columns:

            insert_columns.append("name")
            insert_values.append(name)


        if "description" in columns:

            insert_columns.append("description")
            insert_values.append(description)


        if "date" in columns:

            insert_columns.append("date")
            insert_values.append(date)


        if "venue" in columns:

            insert_columns.append("venue")
            insert_values.append(venue)


        if "image" in columns:

            insert_columns.append("image")
            insert_values.append(image_filename)


        # ----------------------------------------------------
        # LEGACY COLUMNS
        # ----------------------------------------------------

        if "category" in columns:

            insert_columns.append("category")
            insert_values.append("General")


        if "time" in columns:

            insert_columns.append("time")
            insert_values.append("TBD")


        if "location" in columns:

            insert_columns.append("location")
            insert_values.append(venue)


        if "emoji" in columns:

            insert_columns.append("emoji")
            insert_values.append("🎓")


        placeholders = ", ".join(
            ["?"] * len(insert_columns)
        )

        column_string = ", ".join(
            insert_columns
        )


        connection.execute(
            f"""
            INSERT INTO events
            ({column_string})
            VALUES ({placeholders})
            """,
            insert_values
        )


        connection.commit()


    except Exception as error:

        connection.rollback()


        # If database insertion fails,
        # remove the uploaded image.

        if image_filename:

            image_path = os.path.join(
                UPLOAD_FOLDER,
                image_filename
            )


            if os.path.exists(
                image_path
            ):

                os.remove(
                    image_path
                )


        return (
            "Event could not be added: "
            + str(error)
        )


    finally:

        connection.close()


    return redirect(
        url_for("admin")
    )


# ============================================================
# EDIT EVENT
# ============================================================

@app.route(
    "/admin/events/edit/<int:event_id>"
)
def edit_event(event_id):

    if not session.get("admin"):

        return redirect(
            url_for("login")
        )


    connection = get_db_connection()

    try:

        event = connection.execute(
            """
            SELECT *
            FROM events
            WHERE id = ?
            """,
            (event_id,)
        ).fetchone()

    finally:

        connection.close()


    if event is None:

        return "Event not found."


    return render_template(
        "edit_event.html",
        event=event
    )


# ============================================================
# UPDATE EVENT
# ============================================================

@app.route(
    "/admin/events/update/<int:event_id>",
    methods=["POST"]
)
def update_event(event_id):

    if not session.get("admin"):

        return redirect(
            url_for("login")
        )


    name = request.form.get(
        "name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    date = request.form.get(
        "date",
        ""
    ).strip()

    venue = request.form.get(
        "venue",
        ""
    ).strip()


    if not name:
        return "Event name is required."

    if not description:
        return "Event description is required."

    if not date:
        return "Event date is required."

    if not venue:
        return "Event venue is required."


    # --------------------------------------------------------
    # NEW IMAGE
    # --------------------------------------------------------

    image = request.files.get(
        "event_image"
    )

    new_image_filename = None


    if image and image.filename:

        if not allowed_file(
            image.filename
        ):

            return (
                "Invalid image format. "
                "Please upload PNG, JPG, JPEG, GIF or WEBP."
            )


        original_filename = secure_filename(
            image.filename
        )


        filename_without_extension = os.path.splitext(
            original_filename
        )[0]

        extension = os.path.splitext(
            original_filename
        )[1].lower()


        new_image_filename = (
            filename_without_extension
            + "_"
            + str(int(time.time() * 1000))
            + extension
        )


        # Make sure uploads folder exists.

        os.makedirs(
            UPLOAD_FOLDER,
            exist_ok=True
        )


        new_image_path = os.path.join(
            UPLOAD_FOLDER,
            new_image_filename
        )


        image.save(
            new_image_path
        )


    # --------------------------------------------------------
    # DATABASE UPDATE
    # --------------------------------------------------------

    connection = get_db_connection()

    try:

        table_info = connection.execute(
            "PRAGMA table_info(events)"
        ).fetchall()


        columns = [
            column["name"]
            for column in table_info
        ]


        # ----------------------------------------------------
        # GET OLD EVENT
        # ----------------------------------------------------

        old_event = connection.execute(
            """
            SELECT *
            FROM events
            WHERE id = ?
            """,
            (event_id,)
        ).fetchone()


        if old_event is None:

            if new_image_filename:

                new_image_path = os.path.join(
                    UPLOAD_FOLDER,
                    new_image_filename
                )


                if os.path.exists(
                    new_image_path
                ):

                    os.remove(
                        new_image_path
                    )


            return "Event not found."


        old_image_filename = None


        if "image" in old_event.keys():

            old_image_filename = old_event["image"]


        # ----------------------------------------------------
        # PREPARE UPDATE
        # ----------------------------------------------------

        updates = []
        values = []


        if "name" in columns:

            updates.append(
                "name = ?"
            )

            values.append(
                name
            )


        if "description" in columns:

            updates.append(
                "description = ?"
            )

            values.append(
                description
            )


        if "date" in columns:

            updates.append(
                "date = ?"
            )

            values.append(
                date
            )


        if "venue" in columns:

            updates.append(
                "venue = ?"
            )

            values.append(
                venue
            )


        # Only change image if a new image was uploaded.

        if (
            "image" in columns
            and
            new_image_filename
        ):

            updates.append(
                "image = ?"
            )

            values.append(
                new_image_filename
            )


        # ----------------------------------------------------
        # LEGACY COLUMNS
        # ----------------------------------------------------

        if "category" in columns:

            updates.append(
                "category = ?"
            )

            values.append(
                "General"
            )


        if "time" in columns:

            updates.append(
                "time = ?"
            )

            values.append(
                "TBD"
            )


        if "location" in columns:

            updates.append(
                "location = ?"
            )

            values.append(
                venue
            )


        if "emoji" in columns:

            updates.append(
                "emoji = ?"
            )

            values.append(
                "🎓"
            )


        values.append(
            event_id
        )


        update_string = ", ".join(
            updates
        )


        connection.execute(
            f"""
            UPDATE events
            SET {update_string}
            WHERE id = ?
            """,
            values
        )


        connection.commit()


        # ----------------------------------------------------
        # DELETE OLD IMAGE
        # ----------------------------------------------------

        if (
            new_image_filename
            and
            old_image_filename
            and
            old_image_filename != new_image_filename
        ):

            old_image_path = os.path.join(
                UPLOAD_FOLDER,
                old_image_filename
            )


            if os.path.exists(
                old_image_path
            ):

                os.remove(
                    old_image_path
                )


    except Exception as error:

        connection.rollback()


        # Delete newly uploaded image if update failed.

        if new_image_filename:

            new_image_path = os.path.join(
                UPLOAD_FOLDER,
                new_image_filename
            )


            if os.path.exists(
                new_image_path
            ):

                os.remove(
                    new_image_path
                )


        return (
            "Event could not be updated: "
            + str(error)
        )


    finally:

        connection.close()


    return redirect(
        url_for("admin")
    )


# ============================================================
# DELETE EVENT
# ============================================================

@app.route(
    "/admin/events/delete/<int:event_id>",
    methods=["POST"]
)
def delete_event(event_id):

    if not session.get("admin"):

        return redirect(
            url_for("login")
        )


    connection = get_db_connection()

    try:

        # Get event before deleting it.

        event = connection.execute(
            """
            SELECT *
            FROM events
            WHERE id = ?
            """,
            (event_id,)
        ).fetchone()


        connection.execute(
            """
            DELETE FROM events
            WHERE id = ?
            """,
            (event_id,)
        )


        connection.commit()


        # ----------------------------------------------------
        # DELETE ASSOCIATED IMAGE
        # ----------------------------------------------------

        if (
            event
            and
            "image" in event.keys()
        ):

            image_filename = event["image"]


            if image_filename:

                image_path = os.path.join(
                    UPLOAD_FOLDER,
                    image_filename
                )


                if os.path.exists(
                    image_path
                ):

                    os.remove(
                        image_path
                    )


    except Exception as error:

        connection.rollback()

        return (
            "Event could not be deleted: "
            + str(error)
        )


    finally:

        connection.close()


    return redirect(
        url_for("admin")
    )


# ============================================================
# DELETE REGISTRATION
# ============================================================

@app.route(
    "/admin/registrations/delete/<int:registration_id>",
    methods=["POST"]
)
def delete_registration(registration_id):

    if not session.get("admin"):

        return redirect(
            url_for("login")
        )


    connection = get_db_connection()

    try:

        connection.execute(
            """
            DELETE FROM registrations
            WHERE id = ?
            """,
            (registration_id,)
        )


        connection.commit()


    except Exception as error:

        connection.rollback()

        return (
            "Registration could not be deleted: "
            + str(error)
        )


    finally:

        connection.close()


    return redirect(
        url_for("admin")
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.pop(
        "admin",
        None
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    # Make sure upload folder exists every time
    # the application starts.

    os.makedirs(
        UPLOAD_FOLDER,
        exist_ok=True
    )

    create_database()

    fix_database()

    add_default_events()

    app.run(
        debug=True
    )