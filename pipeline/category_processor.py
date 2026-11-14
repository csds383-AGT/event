import bus
import cli_api


def handle(event):
    category = event["category"]
    concerts = category["concert_events"]
    if not isinstance(concerts, list):
        raise ValueError("concert_events must be a list")
    category_id = cli_api.create_category(
        category["category_name"],
        category["description"],
        custom_id=category.get("custom_id"),
    )
    return [{"category_id": category_id, "concert_event": concert} for concert in concerts]


if __name__ == "__main__":
    bus.run("category-processor", handle, emits="category.registered")