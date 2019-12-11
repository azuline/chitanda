CREATE TABLE irc_channels (
    name TEXT,
    server TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (name, server)
);
