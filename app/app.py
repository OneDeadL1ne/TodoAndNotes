import sqlite3
import sys
import webbrowser
from pathlib import Path
from threading import Timer

from flask import Flask, g, redirect, render_template, request, url_for


BASE_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
DB_PATH = BASE_DIR / "database.db"

app = Flask(
    __name__,
    template_folder=str(RESOURCE_DIR / "templates"),
    static_folder=str(RESOURCE_DIR / "static"),
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'done')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.execute(
            "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
            (1, "default_user"),
        )
        if db.execute("SELECT COUNT(*) FROM todos").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO todos (user_id, title, status) VALUES (?, ?, ?)",
                [
                    (1, "Подготовить ER-диаграмму", "active"),
                    (1, "Записать видео-обзор проекта", "active"),
                    (1, "Оформить README", "done"),
                ],
            )
        if db.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO notes (user_id, title, body) VALUES (?, ?, ?)",
                [
                    (
                        1,
                        "Идея интерфейса",
                        "Боковое меню разделяет список дел и бессистемные идеи.",
                    ),
                    (
                        1,
                        "Тема проекта",
                        "Разработка веб-приложения для структурирования мыслей.",
                    ),
                ],
            )
        db.commit()


def get_stats():
    db = get_db()
    notes_count = db.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    todos_count = db.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
    active_count = db.execute(
        "SELECT COUNT(*) FROM todos WHERE status = 'active'"
    ).fetchone()[0]
    done_count = db.execute(
        "SELECT COUNT(*) FROM todos WHERE status = 'done'"
    ).fetchone()[0]
    return {
        "notes": notes_count,
        "todos": todos_count,
        "active": active_count,
        "done": done_count,
    }


@app.route("/")
def index():
    return render_template("index.html", stats=get_stats())


@app.route("/notes", methods=["GET", "POST"])
def notes():
    db = get_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        if title and body:
            db.execute(
                "INSERT INTO notes (user_id, title, body) VALUES (?, ?, ?)",
                (1, title, body),
            )
            db.commit()
        return redirect(url_for("notes"))

    items = db.execute(
        "SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC", (1,)
    ).fetchall()
    return render_template("notes.html", notes=items, stats=get_stats())


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def delete_note(note_id):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, 1))
    db.commit()
    return redirect(url_for("notes"))


@app.route("/todos", methods=["GET", "POST"])
def todos():
    db = get_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            db.execute(
                "INSERT INTO todos (user_id, title, status) VALUES (?, ?, ?)",
                (1, title, "active"),
            )
            db.commit()
        return redirect(url_for("todos"))

    items = db.execute(
        "SELECT * FROM todos WHERE user_id = ? ORDER BY status ASC, created_at DESC",
        (1,),
    ).fetchall()
    return render_template("todos.html", todos=items, stats=get_stats())


@app.route("/todos/<int:todo_id>/toggle", methods=["POST"])
def toggle_todo(todo_id):
    db = get_db()
    todo = db.execute(
        "SELECT status FROM todos WHERE id = ? AND user_id = ?", (todo_id, 1)
    ).fetchone()
    if todo:
        next_status = "done" if todo["status"] == "active" else "active"
        db.execute(
            "UPDATE todos SET status = ? WHERE id = ? AND user_id = ?",
            (next_status, todo_id, 1),
        )
        db.commit()
    return redirect(url_for("todos"))


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
def delete_todo(todo_id):
    db = get_db()
    db.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, 1))
    db.commit()
    return redirect(url_for("todos"))


if __name__ == "__main__":
    init_db()
    Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
