CREATE TABLE lastfm (
    user TEXT,
    listener TEXT,
    lastfm TEXT NOT NULL,
    PRIMARY KEY (user, listener)
);
