import bus
import cli_api


def handle(event):
    artist = event["artist"]
    concerts = artist["concert_events"]
    if not isinstance(concerts, list):
        raise ValueError("concert_events must be a list")
    artist_id = cli_api.create_artist(artist["artist_name"], artist["booking_contact"])
    return [{"artist_id": artist_id, "concert_event": concert} for concert in concerts]


if __name__ == "__main__":
    bus.run("artist-processor", handle, emits="artist.registered")
