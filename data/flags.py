# ISO 3166-1 alpha-2 country codes for flagcdn.com
FLAGS = {
    "Mexico": "mx",
    "South Korea": "kr",
    "Czechia": "cz",
    "South Africa": "za",
    "Bosnia-Herzegovina": "ba",
    "Canada": "ca",
    "Qatar": "qa",
    "Switzerland": "ch",
    "Brazil": "br",
    "Haiti": "ht",
    "Morocco": "ma",
    "Scotland": "gb-sct",
    "Australia": "au",
    "Paraguay": "py",
    "Turkey": "tr",
    "United States": "us",
    "Curaçao": "cw",
    "Germany": "de",
    "Ecuador": "ec",
    "Ivory Coast": "ci",
    "Japan": "jp",
    "Netherlands": "nl",
    "Sweden": "se",
    "Tunisia": "tn",
    "Egypt": "eg",
    "Belgium": "be",
    "Iran": "ir",
    "New Zealand": "nz",
    "Cape Verde Islands": "cv",
    "Saudi Arabia": "sa",
    "Spain": "es",
    "Uruguay": "uy",
    "France": "fr",
    "Iraq": "iq",
    "Norway": "no",
    "Senegal": "sn",
    "Algeria": "dz",
    "Argentina": "ar",
    "Jordan": "jo",
    "Austria": "at",
    "Congo DR": "cd",
    "Colombia": "co",
    "Portugal": "pt",
    "Uzbekistan": "uz",
    "England": "gb-eng",
    "Ghana": "gh",
    "Croatia": "hr",
    "Panama": "pa",
    "Mauritania": "mr",
    "Venezuela": "ve",
    "Indonesia": "id",
    "Ukraine": "ua",
}


def get_flag_url(team_name: str, size: str = "16x12") -> str:
    """Returns flagcdn.com image URL for a team."""
    code = FLAGS.get(team_name, "")
    if not code:
        return ""
    return f"https://flagcdn.com/{size}/{code}.png"


def get_flag_img(team_name: str) -> str:
    """Returns HTML img tag for a team flag."""
    url = get_flag_url(team_name)
    if not url:
        return ""
    return f"<img src='{url}' style='height:12px;vertical-align:middle;margin-right:4px;border:0.5px solid #ddd;'>"


def get_flag(team_name: str) -> str:
    """Backwards compatible — returns flag img tag."""
    return get_flag_img(team_name)