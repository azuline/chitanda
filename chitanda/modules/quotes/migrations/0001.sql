CREATE TABLE quotes (
    id INTEGER,
    channel TEXT,
    listener TEXT,
    quote TEXT NOT NULL COLLATE NOCASE,
    time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    adder TEXT NOT NULL,
    PRIMARY KEY (id, channel, listener)
);
