import bus
import cli_api


def handle(event):
    media = event["media"]
    items = media if isinstance(media, list) else [media]
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("media entries must be objects")
        event_id = item.get("event_id") or event["event_id"]
        cli_api.create_media(
            event_id,
            item["image_url"],
            custom_id=item.get("custom_id"),
        )
    return []


if __name__ == "__main__":
    bus.run("media-processor", handle)