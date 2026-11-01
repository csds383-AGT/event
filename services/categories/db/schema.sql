CREATE TABLE categories
(
    id          UUID PRIMARY KEY DEFAULT uuidv7(),
    name        TEXT             NOT NULL,
    description TEXT             NOT NULL
);
