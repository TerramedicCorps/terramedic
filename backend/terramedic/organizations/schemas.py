from ninja import Schema


class OrganizationOut(Schema):
    id: int
    name: str
    description: str
    website_url: str
    image_url: str
    categories: list[str]
    tags: list[str]
    sort_order: int
