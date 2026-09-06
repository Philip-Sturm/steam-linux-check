from dataclasses import dataclass

from .models import (
    AntiCheatInfo,
    OwnedGame,
    ProtonDBInfo,
    SteamDeckInfo,
    SteamStoreInfo,
)
from .providers.anticheat import get_anticheat_games
from .providers.protondb import get_protondb_info
from .providers.steam_deck import get_steam_deck_info
from .providers.steam_store import get_app_details


@dataclass
class CollectedCompatibilityData:
    """Compatibility data collected from all external providers."""

    store_info_by_app: dict[int, SteamStoreInfo]
    proton_info_by_app: dict[int, ProtonDBInfo]
    anticheat_by_app_id: dict[int, AntiCheatInfo]
    deck_info_by_app: dict[int, SteamDeckInfo]
    native_app_ids: set[int]


def collect_compatibility_data(
    owned_games: list[OwnedGame],
) -> CollectedCompatibilityData:
    """Collect compatibility information for all owned Steam games."""

    # ---------------------------------------------------------
    # Steam Store
    # ---------------------------------------------------------

    print(
        f"\nSteam-Store-Daten werden geprüft: "
        f"{len(owned_games)} Spiele"
    )

    store_infos: list[SteamStoreInfo] = []

    for index, game in enumerate(owned_games, start=1):
        print(
            f"[{index:>3}/{len(owned_games)}] "
            f"{game.name}"
        )

        info = get_app_details(game.app_id)

        if info is not None:
            store_infos.append(info)

    store_info_by_app = {
        info.app_id: info
        for info in store_infos
    }

    native_app_ids = {
        info.app_id
        for info in store_infos
        if info.app_type == "game" and info.linux
    }

    print()
    print(f"Steam-Store-Daten erhalten: {len(store_infos)}")
    print(f"Native Linux-Spiele: {len(native_app_ids)}")

    # ---------------------------------------------------------
    # ProtonDB
    # ---------------------------------------------------------

    proton_targets = [
        game
        for game in owned_games
        if game.app_id not in native_app_ids
    ]

    print(
        f"\nProtonDB-Daten werden geprüft: "
        f"{len(proton_targets)} Spiele"
    )

    proton_infos: list[ProtonDBInfo] = []

    for index, game in enumerate(proton_targets, start=1):
        print(
            f"[{index:>3}/{len(proton_targets)}] "
            f"{game.name}"
        )

        info = get_protondb_info(game.app_id)

        if info is not None:
            proton_infos.append(info)

    proton_info_by_app = {
        info.app_id: info
        for info in proton_infos
    }

    print()
    print(f"ProtonDB-Daten erhalten: {len(proton_infos)}")

    # ---------------------------------------------------------
    # Anti-Cheat
    # ---------------------------------------------------------

    anticheat_games = get_anticheat_games()

    anticheat_by_app_id = {
        game.app_id: game
        for game in anticheat_games
        if game.app_id is not None
    }

    print(
        f"\nAnti-Cheat-Datensätze: "
        f"{len(anticheat_games)}"
    )

    # ---------------------------------------------------------
    # Steam Deck / SteamOS
    # ---------------------------------------------------------

    deck_targets = [
        game
        for game in owned_games
        if game.app_id not in native_app_ids
    ]

    print(
        f"\nSteam-Deck-/SteamOS-Daten werden geprüft: "
        f"{len(deck_targets)} Spiele"
    )

    deck_infos: list[SteamDeckInfo] = []

    for index, game in enumerate(deck_targets, start=1):
        print(
            f"[{index:>3}/{len(deck_targets)}] "
            f"{game.name}"
        )

        info = get_steam_deck_info(game.app_id)

        if info is not None:
            deck_infos.append(info)

    deck_info_by_app = {
        info.app_id: info
        for info in deck_infos
    }

    print()
    print(f"Steam-Deck-Daten erhalten: {len(deck_infos)}")

    # ---------------------------------------------------------
    # Ergebnis
    # ---------------------------------------------------------

    return CollectedCompatibilityData(
        store_info_by_app=store_info_by_app,
        proton_info_by_app=proton_info_by_app,
        anticheat_by_app_id=anticheat_by_app_id,
        deck_info_by_app=deck_info_by_app,
        native_app_ids=native_app_ids,
    )