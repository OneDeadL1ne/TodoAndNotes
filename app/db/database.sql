-- Todos And Notes: схема базы данных и демонстрационные запросы

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



-- Запрос 1. Получить все заметки.
SELECT * FROM notes;

-- Запрос 2. Получить все задачи.
SELECT * FROM todos;

-- Запрос 3. Получить невыполненные задачи.
SELECT * FROM todos WHERE status = 'active';

-- Запрос 4. Подсчитать количество заметок.
SELECT COUNT(*) AS notes_count FROM notes;

-- Запрос 5. Подсчитать задачи по статусам.
SELECT status, COUNT(*) AS todos_count
FROM todos
GROUP BY status;
