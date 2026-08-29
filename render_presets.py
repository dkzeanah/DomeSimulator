"""One-click video render setups for the launcher.

Every video this project publishes was produced by a specific
combination of lesson, action, resolution, frame rate, voice and
segment choices.  Remembering that combination is exactly the kind of
undocumented knowledge that makes a repository impossible for anybody
else to reproduce -- so it lives here instead, as data.

Pick a preset in the launcher's **Video preset** dropdown and every
field on the tab fills in with the exact setup that produced that file.
Press the launch button and you get the same video.  Nothing to
configure, nothing to remember, nothing to get wrong.

Each preset is a plain dict of launcher field values, so a preset can
never drift away from what the launcher actually sends: the same keys
are read straight into the tab's widgets.

The voice settings deserve a note.  Chapter durations are measured off
synthesized speech, so **voice, rate, pitch and volume are part of the
render, not decoration** -- change one and every chapter boundary after
it moves.  That is why each preset states all four explicitly rather
than leaving them at whatever the tab happened to be showing.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# The narration voice every published video in this repository uses.
# Stated here rather than defaulted, because the timeline depends on it.
HOUSE_VOICE = "en-US-AndrewMultilingualNeural"


@dataclass(frozen=True)
class RenderPreset:
    """One reproducible video render, as launcher field values."""

    key: str
    label: str
    summary: str
    """One line the launcher shows when this preset is selected."""
    fields: dict = field(default_factory=dict)
    """Launcher field values. Keys match the Masterclass tab's widgets."""

    def applied(self) -> dict:
        """The full field set, house defaults filled in.

        A preset states what makes it itself; everything else comes from
        the house defaults so that adding a new shared default does not
        mean editing every preset.
        """
        merged = {
            "action": "export_video",
            "lesson": "2v",
            "size": "1920x1080",
            "fps": "30",
            "voice": HOUSE_VOICE,
            "voice_rate": "+0%",
            "voice_pitch": "+0Hz",
            "voice_volume": "+0%",
            "no_narration": False,
            "fullscreen": False,
            "compose_segments": False,
            "segments_include": "",
            "segments_exclude": "",
            "export_video": "",
            "shots": "",
            "voice_preview": "",
        }
        merged.update(self.fields)
        return merged


def _video(key: str, lesson: str, filename: str, summary: str,
           **extra) -> RenderPreset:
    """A full narrated export to the standard deliverables folder."""
    fields = {
        "lesson": lesson,
        "action": "export_video",
        "export_video": f"deliverables/masterclass/{filename}",
    }
    fields.update(extra)
    return RenderPreset(key=key, label=filename, summary=summary,
                        fields=fields)


PRESETS: tuple[RenderPreset, ...] = (
    RenderPreset(
        key="custom",
        label="(no preset -- use the fields below)",
        summary="Nothing is filled in for you; set the fields yourself. "
                "Pick any other preset to reproduce a published video "
                "exactly.",
        # Deliberately the harmless action: selecting the placeholder
        # must never arm an export nobody asked for.
        fields={"action": "run"},
    ),

    # -- the two big ones ---------------------------------------------
    _video("master", "master", "domesim-master-presentation.mp4",
           "THE BIG ONE. Every tool, the whole construction masterclass, "
           "the frankendome, the priced starter home and the factory "
           "case, with 13 math screens deriving every figure on camera. "
           "About 45 minutes; allow a few hours to render."),
    _video("world", "world", "every-dome-in-the-world.mp4",
           "All twelve Dome Creator presets, each rebuilt live from the "
           "simulator's own modules and shown at true relative scale, "
           "with math screens for frequency, framing, price and "
           "efficiency."),

    # -- the teaching lessons -----------------------------------------
    _video("build", "build", "dome-construction-masterclass.mp4",
           "The 46-chapter construction lesson: geometry, cut lists, "
           "jigs, raising, skinning, and the mistakes that stop domes "
           "going up."),
    _video("cuts", "cuts", "hubless-compound-cut.mp4",
           "The single hardest operation in a hubless dome: the compound "
           "cut, on both machines, with the jig between them."),
    _video("hex", "hex", "hex-dome-masterclass.mp4",
           "Hexagonal domes: one strut length, twelve pentagons, and "
           "what raising the frequency costs."),
    _video("zome", "zome", "zome-construction-masterclass.mp4",
           "Zomes: flat parallelogram panels, one strut length, and a "
           "true point on top."),
    _video("line", "line", "assembly-line-energy-masterclass.mp4",
           "What building one dome costs the two people who build it, "
           "limb by limb."),
    _video("franken", "franken", "frankendome-build-v2.mp4",
           "The mixed-stock dome: folded brackets, slack, settling, and "
           "what it actually cost.",
           compose_segments=True),

    # -- the montages and campaign films -------------------------------
    _video("hype6", "hype6", "frankendome-montage-v6.mp4",
           "The Frankendome montage, version six: themed shells, the "
           "four product lines, a faster cadence and a beat under it.",
           voice_rate="+18%", compose_segments=True,
           segments_include="party"),
    _video("kick2", "kick2", "dome-kickstarter-v2.mp4",
           "The campaign film: the brim, the pony wall, running cost, "
           "radiative cooling paint and the ten points.",
           voice_rate="+6%", compose_segments=True,
           segments_include="whoami"),

    # -- quick jobs that are not full exports --------------------------
    RenderPreset(
        key="master_stills",
        label="master presentation -- contact-sheet stills",
        summary="Renders one still every two minutes through the master "
                "presentation, with no narration and no video encode. "
                "The fastest way to see what the film looks like "
                "without waiting hours for it.",
        fields={
            "lesson": "master",
            "action": "shots",
            "shots": ",".join(str(second) for second in
                              range(60, 2640, 120)),
        },
    ),
    RenderPreset(
        key="world_stills",
        label="every dome in the world -- stills",
        summary="A still from each chapter of the twelve-design film. "
                "Quick, and it shows every preset dome without a full "
                "render.",
        fields={
            "lesson": "world",
            "action": "shots",
            "shots": ",".join(str(second) for second in
                              range(20, 620, 20)),
        },
    ),
    RenderPreset(
        key="voice_audition",
        label="audition the house narration voice",
        summary="Generates a short MP3 in the house voice so you can "
                "hear it before committing to a multi-hour render.",
        fields={
            "lesson": "2v",
            "action": "voice_preview",
            "voice_preview": "deliverables/voice-audition.mp3",
        },
    ),
    RenderPreset(
        key="render_all",
        label="rebuild every published video",
        summary="Renders every deliverable in this repository, one at "
                "a time, skipping any that already exist. This is a very "
                "long job -- many hours -- and it is the one that "
                "reproduces the whole published set from a fresh clone.",
        fields={"lesson": "master", "action": "render_all"},
    ),
)


PRESET_BY_KEY = {preset.key: preset for preset in PRESETS}
PRESET_LABELS = [preset.label for preset in PRESETS]
PRESET_BY_LABEL = {preset.label: preset for preset in PRESETS}


def preset_menu() -> str:
    """A plain-text listing, for the log pane and the docs."""
    lines = [f"{len(PRESETS)} video render presets:"]
    for preset in PRESETS:
        lines.append(f"  {preset.key:<16} {preset.label}")
        lines.append(f"                   {preset.summary}")
    return "\n".join(lines)


def validate_render_presets() -> None:
    """Every preset must name a real lesson and a real action."""
    from two_v_demo.lesson_registry import LESSONS

    actions = {
        "run", "selftest", "report", "shots", "export_video",
        "voice_preview", "list_voices", "narration_only", "script",
        "build_packet", "list_lessons", "list_deliverables",
        "list_segments", "soundboard", "render_all",
    }

    keys = [preset.key for preset in PRESETS]
    assert len(set(keys)) == len(keys), "a preset key is repeated"
    labels = [preset.label for preset in PRESETS]
    assert len(set(labels)) == len(labels), "a preset label is repeated"

    for preset in PRESETS:
        applied = preset.applied()
        assert applied["lesson"] in LESSONS, (preset.key, applied["lesson"])
        assert applied["action"] in actions, (preset.key, applied["action"])
        assert preset.summary and len(preset.summary) > 30, preset.key
        # An export must say where the file goes, or it silently lands
        # somewhere nobody looks.
        if applied["action"] == "export_video":
            assert applied["export_video"], preset.key
        if applied["action"] == "shots":
            assert applied["shots"], preset.key

    # Every deliverable this repository publishes should be reachable as
    # a one-click preset, or the promise of "no setup" is only partly
    # true. The archival montages that predate segments are exempt.
    from two_v_demo.deliverables import DELIVERABLES

    covered = {preset.applied()["lesson"] for preset in PRESETS}
    archival = {"hype", "hype2", "hype3", "hype4", "hype5", "kick"}
    missing = {item.lesson for item in DELIVERABLES} - covered - archival
    assert not missing, f"deliverables with no render preset: {sorted(missing)}"
