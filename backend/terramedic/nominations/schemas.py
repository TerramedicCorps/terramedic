from ninja import Schema

from terramedic.organizations.models import Category


class NominationIn(Schema):
    url: str
    categories: list[str]
    notes: str = ""
    website: str = ""  # honeypot field — should always be empty

    def validate_url(self) -> str | None:
        """Return an error message if the URL is invalid, else None."""
        if not self.url:
            return "URL is required."
        if not (
            self.url.startswith("http://") or self.url.startswith("https://")
        ):
            return "URL must start with http:// or https://."
        return None

    def validate_categories(self) -> str | None:
        """Return an error message if categories are invalid, else None."""
        if not self.categories:
            return "At least one category is required."
        valid = set(Category.values)
        for cat in self.categories:
            if cat not in valid:
                return f"Invalid category: {cat}"
        return None


class NominationOut(Schema):
    confirmation_id: str


class NominationStatusOut(Schema):
    confirmation_id: str
    status: str
