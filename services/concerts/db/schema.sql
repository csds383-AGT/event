CREATE TABLE IF NOT EXISTS concert_events (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    available_tickets BIGINT NOT NULL,
    ticket_price BIGINT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL
);

-- Note: db.link() inserts strictly in order, so event_id must be the first column.
CREATE TABLE IF NOT EXISTS bookings (
    event_id UUID NOT NULL REFERENCES concert_events(id) ON DELETE CASCADE,
    artist_id UUID NOT NULL,
    PRIMARY KEY (event_id, artist_id)
);

CREATE TABLE IF NOT EXISTS event_categories (
    event_id UUID NOT NULL REFERENCES concert_events(id) ON DELETE CASCADE,
    category_id UUID NOT NULL,
    PRIMARY KEY (event_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_bookings_artist_id ON bookings(artist_id);
CREATE INDEX IF NOT EXISTS idx_categories_category_id ON event_categories(category_id);