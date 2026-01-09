DROP TABLE IF EXISTS guestbook;
CREATE TABLE guestbook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    location TEXT,
    timestamp TEXT
);
