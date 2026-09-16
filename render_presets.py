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
    _video("world_chatgpt", "world_chatgpt",
           "ten-dome-builds-master-20260829-135242-chatgpt.mp4",
           "The accountable master cut: ten real Dome Creator presets "
           "with Dome Forge and Assembly Line context, a per-build "
           "material breakdown, a construction-event labor breakdown, "
           "and a modeled direct-sale price for each."),

    _video("series", "series", "the-vance-network-mini-series.mp4",
           "All six episodes of the dome micro-drama, back to back: six "
           "cold hooks, six cliffhangers, one arc, and a finale that "
           "leaves a thread open. Rendered 1080x1920.",
           size="1080x1920"),

    _video("drama", "drama", "ep-dome-001-high-council.mp4",
           "EP_DOME_001: a 60-second vertical micro-drama in the dome. "
           "Four beats, five archetypes, and a camera the script "
           "directs. Rendered 1080x1920, because the framing is "
           "computed for 9:16.",
           size="1080x1920"),

    _video("wedge", "wedge", "eight-cuts-to-a-house.mp4",
           "Building the dome straight from the tree: raw 45-degree log "
           "sectors as members, bark out and pith in, forty pinwheel "
           "frames with every end square, and gasketed seams instead of "
           "shared struts. Ten math screens derive the tree's board "
           "feet, the honest 2x4 packing, the kerf, the joint and the "
           "22-foot dome two trees size."),

    # -- the explainer -------------------------------------------------
    _video("scratch", "scratch", "dome-from-scratch-geometry-to-pixels.mp4",
           "From nothing to a lit pixel: the twelve points phi places, "
           "the divide that makes the shape geodesic, the two strut "
           "lengths that fall out, and then the whole rendering chain -- "
           "tubes, normals, the vertex buffer, the camera matrices, the "
           "divide by w, the depth buffer, culling and the lighting sum. "
           "18 math screens derive every figure on camera."),

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

    _video("look", "look", "dome-house-lookbook.mp4",
           "Two furnished domes, a cast of eight, hair built as strands, "
           "a wardrobe lofted from the body, and the composer refusing "
           "a fitting pod the shell has come down on."),

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
        key="look_stills",
        label="dome house lookbook -- contact-sheet stills",
        summary="One still from each of the lookbook's eleven chapters, "
                "with no narration and no video encode. The fast way to "
                "check the cast, the wardrobe and the composer shots "
                "before rendering the film.",
        fields={
            "lesson": "look",
            "action": "shots",
            "shots": "8,24,40,57,74,92,106,122,139,156,172",
            "no_narration": True,
        },
    ),

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
        key="scratch_stills",
        label="from scratch -- one still per chapter",
        summary="A still from roughly each chapter of the from-scratch "
                "explainer, with no narration and no video encode. The "
                "quick way to check every diagram in the film without "
                "waiting for a full render.",
        fields={
            "lesson": "scratch",
            "action": "shots",
            "shots": ",".join(str(second) for second in
                              range(12, 1740, 38)),
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
    _video("why", "why", "why-wedges-no-sawmill.mp4",
           "The combined wedge film: the frankendome and V brackets it "
           "grew out of, the mechanism chapters borrowed whole from "
           "`wedge`, and then the case -- two timed cutting sessions "
           "cross-checked against a geometric prediction, a wedge "
           "valued two independent ways, the store-bought overheads "
           "nobody counts, and a structural claim given as a crossover "
           "diameter rather than a verdict. 39 chapters, 16 math "
           "screens, about 21 minutes."),

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
    _video("harvest", "harvest", "two-trees-all-at-once.mp4",
           "Registered by the project agent repair step: the harvest lesson was in the registry without a deliverable entry."),
    _video("pine_value", "pine_value", "the-20-dollar-pine.mp4",
           "Registered by the project agent repair step: the pine_value lesson was in the registry without a deliverable entry."),
    _video("why_build", "why_build", "why-build-this-way.mp4",
           "Registered by the project agent repair step: the why_build lesson was in the registry without a deliverable entry."),
    _video("pvtwo", "pvtwo", "pvtwo-masterclass.mp4",
           "Generated by the project agent film recipe: The Twenty Dollar Pine, Part Two."),
    _video("all_domes", "all_domes", "all-domes-every-permutation.mp4",
           "ALL DOMES. Every Dome Creator preset drawn by the Creator's own "
           "renderer -- wood grain, glass, mirror tiles, real foundations and "
           "the equipment inside -- one dome assembled step by step in the "
           "tool's own construction order, then a sweep of every menu the "
           "customizer has, eight domes drawn at random, and the arithmetic of "
           "how many buildings that adds up to.",
           compose_segments=True),

    RenderPreset(
        key="all_domes_stills",
        label="all domes -- one still per chapter",
        summary="A still from each chapter of the Dome Creator showcase, with "
                "no narration and no video encode. The quick way to check "
                "every dome, sweep and cut-away before committing to the full "
                "render.",
        fields={
            "lesson": "all_domes",
            "action": "shots",
            "shots": ",".join(str(second) for second in range(8, 600, 14)),
        },
    ),
    _video("dome_park", "dome_park", "dome-park-bring-your-own-home.mp4",
           "DOME PARK. The Kickstarter cut: an RV park for houses. A host "
           "builds a serviced pad, a dome owner brings the home and plugs in. "
           "Every pad and dome is drawn by the Dome Creator's own renderer, "
           "every figure comes from the park model -- including the ones that "
           "argue against the idea, which are on camera with the rest.",
           compose_segments=True),

    RenderPreset(
        key="dome_park_stills",
        label="dome park -- one still per chapter",
        summary="A still from each chapter of the dome park pitch, with no "
                "narration and no video encode. The quick way to check every "
                "pad, landing, sweep and worksheet before committing to the "
                "full render.",
        fields={
            "lesson": "dome_park",
            "action": "shots",
            "shots": ",".join(str(second) for second in range(8, 580, 22)),
        },
    ),

    # Bring Your Own Dome has its own staged renderer as well
    # (render_bring_your_own_dome.py: audio, render and mux as separate,
    # resumable steps, with recorded takes allowed). This preset is the
    # one-click path through the launcher. Segments stay off: the lesson
    # carries its own contact outro, and splicing the shared one as well
    # would end the film twice.
    _video("byod", "byod", "bring-your-own-dome.mp4",
           "BRING YOUR OWN DOME. The revised pitch: the animated iris pad, "
           "central services, movable partitions, wedge channels, staged "
           "growth and a starter-first budget, with the personal story and "
           "the proposed rewards. Ends on its own contact outro.",
           compose_segments=False),

    RenderPreset(
        key="byod_stills",
        label="bring your own dome -- one still per chapter",
        summary="A still from each chapter of Bring Your Own Dome, with no "
                "narration and no video encode. The quick way to look at "
                "every iris, room layout and title card before committing to "
                "the full render.",
        fields={
            "lesson": "byod",
            "action": "shots",
            "shots": ",".join(str(second) for second in range(8, 587, 15)),
        },
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
