from .models import (
    CompatibilityResult,
    CompatibilityStatus,
    OwnedGame,
    ProtonDBInfo,
    SteamStoreInfo,
)


def evaluate_compatibility(
    game: OwnedGame,
    store_info: SteamStoreInfo | None,
    proton_info: ProtonDBInfo | None,
) -> CompatibilityResult:
    """Evaluate Linux compatibility from currently available providers."""

    if store_info is not None and store_info.linux:
        return CompatibilityResult(
            app_id=game.app_id,
            name=game.name,
            status=CompatibilityStatus.NATIVE,
            reason="Official native Linux build",
        )

    if proton_info is None:
        return CompatibilityResult(
            app_id=game.app_id,
            name=game.name,
            status=CompatibilityStatus.UNKNOWN,
            reason="No ProtonDB data",
        )

    if proton_info.tier == "borked":
        return CompatibilityResult(
            app_id=game.app_id,
            name=game.name,
            status=CompatibilityStatus.BROKEN,
            reason="ProtonDB rating: borked",
        )

    if (
        proton_info.trending_tier == "borked"
        and proton_info.confidence == "strong"
    ):
        return CompatibilityResult(
            app_id=game.app_id,
            name=game.name,
            status=CompatibilityStatus.BROKEN,
            reason="ProtonDB trending rating: borked",
        )

    if proton_info.tier in {"platinum", "gold"}:
        return CompatibilityResult(
            app_id=game.app_id,
            name=game.name,
            status=CompatibilityStatus.WORKS,
            reason=f"ProtonDB rating: {proton_info.tier}",
        )

    if proton_info.tier in {"silver", "bronze"}:
        return CompatibilityResult(
            app_id=game.app_id,
            name=game.name,
            status=CompatibilityStatus.PARTIAL,
            reason=f"ProtonDB rating: {proton_info.tier}",
        )

    return CompatibilityResult(
        app_id=game.app_id,
        name=game.name,
        status=CompatibilityStatus.UNKNOWN,
        reason="Insufficient compatibility data",
    )