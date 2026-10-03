"""Language adapters for Lyrics processing."""

from importlib import import_module
import re
from fluency.lyrics.languages.base import LyricsLanguageAdapter
from fluency.lyrics.languages.spanish import SpanishLyricsAdapter
from fluency.lyrics.languages.spanish_routing import SpanishLiveRouter, SpanishRoutingResources


def load_lyrics_adapter(language: str, **kwargs: object) -> LyricsLanguageAdapter:
    if language == "es":
        return SpanishLyricsAdapter(**kwargs)
    from pkgutil import iter_modules
    from pathlib import Path
    if re.fullmatch(r"[a-z]{2,3}", language):
        for info in iter_modules([str(Path(__file__).parent)]):
            if info.name in {"base", "spanish", "spanish_routing"}:
                continue
            module = import_module(f"{__package__}.{info.name}")
            adapter = getattr(module, "ADAPTER_CLASS", None)
            if adapter is not None and adapter.language == language:
                return adapter(**kwargs)
    raise ValueError(f"no Lyrics processing adapter is installed for language {language!r}")


def load_live_lyrics_router(language: str, **kwargs: object) -> SpanishLiveRouter:
    if language == "es":
        return SpanishLiveRouter(**kwargs)
    raise ValueError(f"no live Lyrics router is installed for language {language!r}")


def load_live_lyrics_routing_resources(
    language: str, **kwargs: object
) -> SpanishRoutingResources:
    if language == "es":
        return SpanishRoutingResources.load(**kwargs)
    raise ValueError(f"no live Lyrics routing resources are installed for language {language!r}")
