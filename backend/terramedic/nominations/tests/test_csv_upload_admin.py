import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from terramedic.nominations.models import Nomination


@pytest.fixture
def admin_user() -> User:
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="testpass123",
    )


@pytest.fixture
def admin_client(admin_user: User) -> Client:
    client = Client()
    client.force_login(admin_user)
    return client


UPLOAD_URL = "/admin/nominations/nomination/upload-csv/"


def _csv_file(content: str, filename: str = "test.csv") -> SimpleUploadedFile:
    return SimpleUploadedFile(
        filename,
        content.encode("utf-8"),
        content_type="text/csv",
    )


@pytest.mark.django_db
class TestUploadCsvViewAccess:
    def test_anonymous_user_redirected(self) -> None:
        client = Client()
        response = client.get(UPLOAD_URL)
        assert response.status_code == 302

    def test_non_staff_user_redirected(self) -> None:
        user = User.objects.create_user(
            username="regular",
            password="testpass123",
        )
        client = Client()
        client.force_login(user)
        response = client.get(UPLOAD_URL)
        assert response.status_code == 302

    def test_staff_without_add_permission_denied(self) -> None:
        user = User.objects.create_user(
            username="staff_no_add",
            password="testpass123",
            is_staff=True,
        )
        client = Client()
        client.force_login(user)
        response = client.get(UPLOAD_URL)
        assert response.status_code == 403


@pytest.mark.django_db
class TestUploadCsvViewGet:
    def test_get_renders_upload_form(self, admin_client: Client) -> None:
        response = admin_client.get(UPLOAD_URL)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Upload CSV" in content
        assert 'type="file"' in content

    def test_changelist_has_upload_link(self, admin_client: Client) -> None:
        response = admin_client.get("/admin/nominations/nomination/")
        content = response.content.decode()
        assert "upload-csv" in content


@pytest.mark.django_db
class TestUploadCsvViewPost:
    def test_valid_csv_creates_nominations(self, admin_client: Client) -> None:
        csv_content = "url,category\nhttps://example.org/,volunteer\nhttps://donate.org/,donate\n"
        response = admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file(csv_content)},
        )
        assert response.status_code == 302  # redirect to changelist
        assert Nomination.objects.count() == 2

    def test_created_nominations_have_empty_ip_hash(
        self,
        admin_client: Client,
    ) -> None:
        csv_content = "url,category\nhttps://example.org/,volunteer\n"
        admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file(csv_content)},
        )
        nom = Nomination.objects.first()
        assert nom is not None
        assert nom.ip_hash is None

    def test_created_nominations_have_csv_upload_note(
        self,
        admin_client: Client,
        admin_user: User,
    ) -> None:
        csv_content = "url,category\nhttps://example.org/,volunteer\n"
        admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file(csv_content)},
        )
        nom = Nomination.objects.first()
        assert nom is not None
        assert "csv upload" in nom.notes.lower()
        assert admin_user.username in nom.notes

    def test_multi_category_row(self, admin_client: Client) -> None:
        csv_content = 'url,category\nhttps://example.org/,"volunteer,donate"\n'
        admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file(csv_content)},
        )
        nom = Nomination.objects.first()
        assert nom is not None
        assert set(nom.categories) == {"volunteer", "donate"}

    def test_invalid_csv_shows_errors(self, admin_client: Client) -> None:
        csv_content = "url,category\nnot-a-url,volunteer\n"
        response = admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file(csv_content)},
        )
        assert response.status_code == 200  # re-renders form with errors
        assert Nomination.objects.count() == 0
        content = response.content.decode()
        assert "error" in content.lower()

    def test_no_file_uploaded_shows_error(self, admin_client: Client) -> None:
        response = admin_client.post(UPLOAD_URL, {})
        assert response.status_code == 200
        content = response.content.decode()
        assert "error" in content.lower()

    def test_non_utf8_file_shows_error(self, admin_client: Client) -> None:
        latin1_bytes = "url,category\nhttps://example.org/,volunt\xe9er\n".encode(
            "latin-1",
        )
        uploaded = SimpleUploadedFile(
            "test.csv", latin1_bytes, content_type="text/csv",
        )
        response = admin_client.post(UPLOAD_URL, {"csv_file": uploaded})
        assert response.status_code == 200
        content = response.content.decode()
        assert "utf-8" in content.lower()

    def test_non_csv_extension_shows_error(self, admin_client: Client) -> None:
        response = admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file("url,category\n", filename="test.txt")},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "csv" in content.lower()

    def test_oversized_file_shows_error(self, admin_client: Client) -> None:
        header = "url,category\n"
        padding = "a" * (1024 * 1024 + 1 - len(header))  # just over 1 MB
        response = admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file(header + padding)},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "size" in content.lower()
        assert Nomination.objects.count() == 0

    def test_too_many_rows_shows_error(self, admin_client: Client) -> None:
        rows = "\n".join(
            f"https://example{i}.org/,volunteer" for i in range(501)
        )
        csv_content = f"url,category\n{rows}\n"
        response = admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file(csv_content)},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "500" in content
        assert Nomination.objects.count() == 0

    def test_duplicate_url_in_db_shows_error(self, admin_client: Client) -> None:
        Nomination.objects.create(
            url="https://existing.org/",
            categories=["volunteer"],
            ip_hash="somehash",
        )
        csv_content = "url,category\nhttps://existing.org/,donate\n"
        response = admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file(csv_content)},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "already exists" in content.lower()
        # Should not create a duplicate
        assert Nomination.objects.count() == 1

    def test_success_message_shows_count(self, admin_client: Client) -> None:
        csv_content = "url,category\nhttps://a.org/,volunteer\nhttps://b.org/,donate\n"
        response = admin_client.post(
            UPLOAD_URL,
            {"csv_file": _csv_file(csv_content)},
            follow=True,
        )
        content = response.content.decode()
        assert "2" in content
