from ninja import Schema

from terramedic.organizations.models import Category


class OrganizationOut(Schema):
    id: int
    name: str
    description: str
    action_text: str
    website_url: str
    image_url: str
    category: Category
    tags: list[str]
    sort_order: int
