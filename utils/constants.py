from collections import namedtuple
from pathlib import Path

from discord import Colour

BASE_DIR = Path(__file__).resolve().parent.parent
DISCORD_MAX_BODY_LENGTH = 2000
SERVER_HOST_NAME = "homies.serveminecraft.net"
GOOGLE_API_SECRETS = BASE_DIR / "client_secrets.json"
EMBED_COLORS = {
    "loading": Colour.gold(),
    "ready": Colour.blue(),
    "error": Colour.red(),
}
LOADING_MESSAGES = ["Hold on a sec", "What are you waiting for?"]
GUILD_CONFIG_VARIABLES = ["cinema_channel_id", "cinema_role_id"]
TRUSTED_GUILD_IDS = [829422702968045568, 691057767024295997]

AternosStatus = namedtuple(
    "AternosStatus", ["online", "offline", "preparing", "loading", "starting"]
)

ATERNOS_STATUS = AternosStatus(
    offline="Offline",
    online="Online",
    preparing="Preparing ...",
    loading="Loading ...",
    starting="Starting ...",
)
