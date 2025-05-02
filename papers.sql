CREATE TABLE papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    abstract TEXT,
    keywords TEXT,
    source TEXT,
    year INTEGER,
    field TEXT,
    pdf_filename TEXT
);
