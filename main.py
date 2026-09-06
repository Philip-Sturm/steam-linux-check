from collections import Counter

from steam_linux_check.compatibility import evaluate_compatibility
from steam_linux_check.providers.anticheat import get_anticheat_games
from steam_linux_check.providers.protondb import get_protondb_info
from steam_linux_check.providers.steam import get_owned_games
from steam_linux_check.providers.steam_deck import (
    category_name,
    get_steam_deck_info,
)
from steam_linux_check.providers.steam_store import get_app_details
from steam_linux_check.steam_detector import (
    find_installed_apps,
    find_steam_installation,
    find_steam_libraries,
    find_steam_user_id,
)


def main() -> None:
    # ---------------------------------------------------------
    # Lokale Steam-Installation
    # ---------------------------------------------------------

    steam_path = find_steam_installation()

    if steam_path is None:
        print("Steam-Installation wurde nicht gefunden.")
        return

    print(f"Steam gefunden: {steam_path}")

    steam_id = find_steam_user_id(steam_path)

    if steam_id is None:
        print("SteamID64 wurde nicht gefunden.")
        return

    print(f"SteamID64: {steam_id}")

    # ---------------------------------------------------------
    # Besitzbibliothek
    # ---------------------------------------------------------

    owned_games = get_owned_games(steam_id)

    print(f"\nBesessene Steam-Spiele: {len(owned_games)}")

    # ---------------------------------------------------------
    # Steam Store
    # ---------------------------------------------------------

    print(
        f"\nSteam-Store-Daten werden geprüft: "
        f"{len(owned_games)} Spiele"
    )

    store_infos = []

    for index, game in enumerate(owned_games, start=1):
        print(
            f"[{index:>3}/{len(owned_games)}] "
            f"{game.name}"
        )

        details = get_app_details(game.app_id)

        if details is not None:
            store_infos.append(details)

    native_games = [
        game
        for game in store_infos
        if game.app_type == "game" and game.linux
    ]

    native_app_ids = {
        game.app_id
        for game in native_games
    }

    print()
    print(f"Steam-Store-Daten erhalten: {len(store_infos)}")
    print(f"Native Linux-Spiele: {len(native_games)}")

    # ---------------------------------------------------------
    # Fehlende Steam-Store-Daten
    # ---------------------------------------------------------

    store_app_ids = {
        info.app_id
        for info in store_infos
    }

    missing_store_games = [
        game
        for game in owned_games
        if game.app_id not in store_app_ids
    ]

    if missing_store_games:
        print(
            f"\nKeine Steam-Store-Daten: "
            f"{len(missing_store_games)}"
        )

        for game in sorted(
            missing_store_games,
            key=lambda game: game.name.lower(),
        ):
            print(
                f"  {game.app_id:<10} "
                f"{game.name}"
            )

    # ---------------------------------------------------------
    # ProtonDB
    # ---------------------------------------------------------

    print("\nProtonDB-Daten werden geprüft...")

    proton_targets = [
        game
        for game in owned_games
        if game.app_id not in native_app_ids
    ]

    proton_infos = []

    for index, game in enumerate(proton_targets, start=1):
        print(
            f"[{index:>3}/{len(proton_targets)}] "
            f"{game.name}"
        )

        info = get_protondb_info(game.app_id)

        if info is not None:
            proton_infos.append(info)

    print()
    print(
        f"ProtonDB-relevante Spiele: "
        f"{len(proton_targets)}"
    )
    print(
        f"ProtonDB-Daten erhalten: "
        f"{len(proton_infos)}"
    )

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

    print(
        "\nSteam-Deck-/SteamOS-Daten "
        "werden geprüft..."
    )

    deck_targets = [
        game
        for game in owned_games
        if game.app_id not in native_app_ids
    ]

    deck_infos = []

    for index, game in enumerate(deck_targets, start=1):
        print(
            f"[{index:>3}/{len(deck_targets)}] "
            f"{game.name}"
        )

        info = get_steam_deck_info(game.app_id)

        if info is not None:
            deck_infos.append(info)

    print()
    print(
        f"Steam-Deck-relevante Spiele: "
        f"{len(deck_targets)}"
    )
    print(
        f"Steam-Deck-Daten erhalten: "
        f"{len(deck_infos)}"
    )

    # ---------------------------------------------------------
    # Provider-Daten nach AppID indizieren
    # ---------------------------------------------------------

    store_info_by_app = {
        info.app_id: info
        for info in store_infos
    }

    proton_info_by_app = {
        info.app_id: info
        for info in proton_infos
    }

    deck_info_by_app = {
        info.app_id: info
        for info in deck_infos
    }

    owned_game_by_app = {
        game.app_id: game
        for game in owned_games
    }

    # ---------------------------------------------------------
    # Compatibility Engine
    # ---------------------------------------------------------

    compatibility_results = []

    for game in owned_games:
        result = evaluate_compatibility(
            game=game,
            store_info=store_info_by_app.get(game.app_id),
            proton_info=proton_info_by_app.get(game.app_id),
            anticheat_info=anticheat_by_app_id.get(game.app_id),
            deck_info=deck_info_by_app.get(game.app_id),
        )

        compatibility_results.append(result)

    status_counts = Counter(
        result.status.value
        for result in compatibility_results
    )

    print("\nCompatibility Summary:")

    for status in [
        "Native",
        "Works",
        "Partial",
        "Broken",
        "Unknown",
    ]:
        print(
            f"  {status:<8} "
            f"{status_counts[status]}"
        )

    # ---------------------------------------------------------
    # Bekannte Testfälle
    # ---------------------------------------------------------

    print("\nTestfälle:")

    test_app_ids = {
        620,       # Portal 2
        2406770,   # Bodycam
        1867240,   # WARDOGS
        976730,    # Halo MCC
        578080,    # PUBG
        359550,    # Rainbow Six Siege
    }

    for result in compatibility_results:
        if result.app_id in test_app_ids:
            print(
                f"  {result.name:<35} "
                f"{result.status.value:<8} "
                f"{result.reason}"
            )

    # ---------------------------------------------------------
    # SteamOS Summary
    # ---------------------------------------------------------

    steamos_counts = Counter(
        category_name(info.steamos_category)
        for info in deck_infos
    )

    print("\nSteamOS Summary:")

    for status in [
        "Verified",
        "Playable",
        "Unsupported",
        "Unknown",
    ]:
        print(
            f"  {status:<12} "
            f"{steamos_counts[status]}"
        )

    # ---------------------------------------------------------
    # SteamOS / ProtonDB Konfliktanalyse
    # ---------------------------------------------------------

    proton_good_steamos_bad = []
    proton_bad_steamos_good = []

    for app_id, deck_info in deck_info_by_app.items():
        proton_info = proton_info_by_app.get(app_id)

        if proton_info is None:
            continue

        game = owned_game_by_app.get(app_id)

        if game is None:
            continue

        steamos_status = category_name(
            deck_info.steamos_category
        )

        proton_tier = proton_info.tier

        if (
            proton_tier in {"gold", "platinum"}
            and steamos_status == "Unsupported"
        ):
            proton_good_steamos_bad.append(
                (
                    game,
                    proton_tier,
                    steamos_status,
                )
            )

        if (
            proton_tier
            in {"bronze", "silver", "borked"}
            and steamos_status == "Playable"
        ):
            proton_bad_steamos_good.append(
                (
                    game,
                    proton_tier,
                    steamos_status,
                )
            )

    print(
        "\nProtonDB Gold/Platinum "
        f"+ SteamOS Unsupported: "
        f"{len(proton_good_steamos_bad)}"
    )

    for (
        game,
        proton_tier,
        steamos_status,
    ) in proton_good_steamos_bad:
        print(
            f"  {game.name:<40} "
            f"ProtonDB={proton_tier:<10} "
            f"SteamOS={steamos_status}"
        )

    print(
        "\nProtonDB Bronze/Silver/Borked "
        f"+ SteamOS Playable: "
        f"{len(proton_bad_steamos_good)}"
    )

    for (
        game,
        proton_tier,
        steamos_status,
    ) in proton_bad_steamos_good:
        print(
            f"  {game.name:<40} "
            f"ProtonDB={proton_tier:<10} "
            f"SteamOS={steamos_status}"
        )

    # ---------------------------------------------------------
    # Lokale Steam-Bibliotheken
    # ---------------------------------------------------------

    libraries = find_steam_libraries(steam_path)

    print("\nSteam-Bibliotheken:")

    for library in libraries:
        print(f"  - {library}")

    apps = find_installed_apps(libraries)

    print(
        f"\nInstallierte Steam-Apps: "
        f"{len(apps)}"
    )

    for app in sorted(
        apps,
        key=lambda app: app.name.lower(),
    ):
        print(
            f"  {app.app_id:<10} "
            f"{app.name}"
        )


if __name__ == "__main__":
    main()