CREATE TABLE IF NOT EXISTS media
(
    id        UUID PRIMARY KEY DEFAULT uuidv7(),
    event_id  UUID             NOT NULL,
    image_url TEXT             NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_media_event_id ON media(event_id);