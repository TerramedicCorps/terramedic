from typing import Any

from django.core.validators import RegexValidator
from django.db import models

# ISO 3166-1 alpha-2 → continent mapping.
# Source: https://en.wikipedia.org/wiki/List_of_sovereign_states_and_dependent_territories_by_continent
COUNTRY_TO_CONTINENT: dict[str, str] = {
    # Africa
    "AO": "Africa", "BF": "Africa", "BI": "Africa", "BJ": "Africa",
    "BW": "Africa", "CD": "Africa", "CF": "Africa", "CG": "Africa",
    "CI": "Africa", "CM": "Africa", "CV": "Africa", "DJ": "Africa",
    "DZ": "Africa", "EG": "Africa", "EH": "Africa", "ER": "Africa",
    "ET": "Africa", "GA": "Africa", "GH": "Africa", "GM": "Africa",
    "GN": "Africa", "GQ": "Africa", "GW": "Africa", "KE": "Africa",
    "KM": "Africa", "LR": "Africa", "LS": "Africa", "LY": "Africa",
    "MA": "Africa", "MG": "Africa", "ML": "Africa", "MR": "Africa",
    "MU": "Africa", "MW": "Africa", "MZ": "Africa", "NA": "Africa",
    "NE": "Africa", "NG": "Africa", "RE": "Africa", "RW": "Africa",
    "SC": "Africa", "SD": "Africa", "SH": "Africa", "SL": "Africa",
    "SN": "Africa", "SO": "Africa", "SS": "Africa", "ST": "Africa",
    "SZ": "Africa", "TD": "Africa", "TG": "Africa", "TN": "Africa",
    "TZ": "Africa", "UG": "Africa", "YT": "Africa", "ZA": "Africa",
    "ZM": "Africa", "ZW": "Africa",
    # Asia
    "AE": "Asia", "AF": "Asia", "AM": "Asia", "AZ": "Asia",
    "BD": "Asia", "BH": "Asia", "BN": "Asia", "BT": "Asia",
    "CN": "Asia", "CY": "Asia", "GE": "Asia", "HK": "Asia",
    "ID": "Asia", "IL": "Asia", "IN": "Asia", "IQ": "Asia",
    "IR": "Asia", "JO": "Asia", "JP": "Asia", "KG": "Asia",
    "KH": "Asia", "KP": "Asia", "KR": "Asia", "KW": "Asia",
    "KZ": "Asia", "LA": "Asia", "LB": "Asia", "LK": "Asia",
    "MM": "Asia", "MN": "Asia", "MO": "Asia", "MV": "Asia",
    "MY": "Asia", "NP": "Asia", "OM": "Asia", "PH": "Asia",
    "PK": "Asia", "PS": "Asia", "QA": "Asia", "SA": "Asia",
    "SG": "Asia", "SY": "Asia", "TH": "Asia", "TJ": "Asia",
    "TL": "Asia", "TM": "Asia", "TR": "Asia", "TW": "Asia",
    "UZ": "Asia", "VN": "Asia", "YE": "Asia",
    # Europe
    "AD": "Europe", "AL": "Europe", "AT": "Europe", "BA": "Europe",
    "BE": "Europe", "BG": "Europe", "BY": "Europe", "CH": "Europe",
    "CZ": "Europe", "DE": "Europe", "DK": "Europe", "EE": "Europe",
    "ES": "Europe", "FI": "Europe", "FO": "Europe", "FR": "Europe",
    "GB": "Europe", "GG": "Europe", "GI": "Europe", "GR": "Europe",
    "HR": "Europe", "HU": "Europe", "IE": "Europe", "IM": "Europe",
    "IS": "Europe", "IT": "Europe", "JE": "Europe", "LI": "Europe",
    "LT": "Europe", "LU": "Europe", "LV": "Europe", "MC": "Europe",
    "MD": "Europe", "ME": "Europe", "MK": "Europe", "MT": "Europe",
    "NL": "Europe", "NO": "Europe", "PL": "Europe", "PT": "Europe",
    "RO": "Europe", "RS": "Europe", "RU": "Europe", "SE": "Europe",
    "SI": "Europe", "SK": "Europe", "SM": "Europe", "UA": "Europe",
    "VA": "Europe", "XK": "Europe",
    # North America
    "AG": "North America", "AI": "North America", "AW": "North America",
    "BB": "North America", "BL": "North America", "BM": "North America",
    "BQ": "North America", "BS": "North America", "BZ": "North America",
    "CA": "North America", "CR": "North America", "CU": "North America",
    "CW": "North America", "DM": "North America", "DO": "North America",
    "GD": "North America", "GL": "North America", "GP": "North America",
    "GT": "North America", "HN": "North America", "HT": "North America",
    "JM": "North America", "KN": "North America", "KY": "North America",
    "LC": "North America", "MF": "North America", "MQ": "North America",
    "MS": "North America", "MX": "North America", "NI": "North America",
    "PA": "North America", "PM": "North America", "PR": "North America",
    "SV": "North America", "SX": "North America", "TC": "North America",
    "TT": "North America", "US": "North America", "VC": "North America",
    "VG": "North America", "VI": "North America",
    # Oceania
    "AS": "Oceania", "AU": "Oceania", "CK": "Oceania", "FJ": "Oceania",
    "FM": "Oceania", "GU": "Oceania", "KI": "Oceania", "MH": "Oceania",
    "MP": "Oceania", "NC": "Oceania", "NF": "Oceania", "NR": "Oceania",
    "NU": "Oceania", "NZ": "Oceania", "PF": "Oceania", "PG": "Oceania",
    "PN": "Oceania", "PW": "Oceania", "SB": "Oceania", "TK": "Oceania",
    "TO": "Oceania", "TV": "Oceania", "VU": "Oceania", "WF": "Oceania",
    "WS": "Oceania",
    # South America
    "AR": "South America", "BO": "South America", "BR": "South America",
    "CL": "South America", "CO": "South America", "EC": "South America",
    "FK": "South America", "GF": "South America", "GY": "South America",
    "PE": "South America", "PY": "South America", "SR": "South America",
    "UY": "South America", "VE": "South America",
    # Antarctica
    "AQ": "Antarctica",
}


class OperatingRegion(models.Model):
    country_code = models.CharField(
        max_length=2,
        validators=[
            RegexValidator(
                r"^[A-Z]{2}$",
                "Must be an ISO 3166-1 alpha-2 code.",
            ),
        ],
    )
    region_code = models.CharField(max_length=10, blank=True, default="")
    name = models.CharField(max_length=200)
    continent = models.CharField(max_length=20, blank=True, default="")

    class Meta:
        ordering = ["country_code", "name"]
        constraints = [
            # region_code defaults to "" for country-level entries, so this
            # allows at most one country-level row per country code while
            # still permitting multiple sub-national regions.
            models.UniqueConstraint(
                fields=["country_code", "region_code"],
                name="unique_country_region",
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.continent = COUNTRY_TO_CONTINENT.get(self.country_code, "")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
