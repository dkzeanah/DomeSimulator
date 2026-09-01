"""Episode schema, cast, and the script parser for the CNEE.

An episode is data: a dome preset, a lighting theme, and a list of beats
that each carry a camera instruction, some rig cues and one line of
dialogue.  This module turns the specification's JSON into typed objects
and then refuses the ones that cannot be shot.

The checks are the point.  A micro-drama fails in specific, boring ways
-- beats that do not join up, a line too long to say in the time it is
given, a rig action nobody implemented, an anchor that does not exist in
the dome -- and each of those is cheaper to catch here than after a
render.  :func:`validate_drama_script` runs them against the
specification's own example episode, so the published script is proof
rather than illustration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .drama_camera import SHOTS
from .drama_rig import ACTIONS
from .drama_stage import DOME_PRESETS, stage_anchors


# ----------------------------------------------------------------------
# The cast
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class Character:
    """One of the recurring archetypes."""

    character_id: str
    name: str
    archetype: str
    look: str
    motivation: str
    default_actions: tuple[str, ...]
    home_anchor: str
    voice_id: str
    stature_m: float = 1.78


CAST: dict[str, Character] = {
    "CHAR_LEO": Character(
        character_id="CHAR_LEO",
        name="Leo Vance",
        archetype="Protagonist / secret heir",
        look="Twenties, rugged wear over a high-tech jumpsuit, grease on "
             "the jaw, focused eyes.",
        motivation="Disgraced dome mechanic and rightful heir to the "
                   "Geodesic Infrastructure Network, proving his work "
                   "against public humiliation.",
        default_actions=("RIG_CLENCH_FIST_RAISE", "RIG_INVASIVE_STEP"),
        home_anchor="DOME_FLOOR_CENTER",
        voice_id="VO_LEO_DEFIANT",
        stature_m=1.80,
    ),
    "CHAR_AURELIA": Character(
        character_id="CHAR_AURELIA",
        name="Aurelia Vance",
        archetype="High-status catalyst",
        look="Late twenties, sharp tailored coat, cold jewellery, "
             "high-contrast posture.",
        motivation="Corporate heiress bound to Leo by an arranged "
                   "agreement, and the first to recognise what he is "
                   "worth.",
        default_actions=("RIG_DISDAINFUL_TURN", "RIG_SLAP_EXECUTE",
                         "RIG_GASP_REACTION"),
        home_anchor="DOME_CURVED_WALL_NORTH",
        voice_id="VO_AURELIA_ANGRY",
        stature_m=1.70,
    ),
    "CHAR_SILAS": Character(
        character_id="CHAR_SILAS",
        name="Master Silas",
        archetype="Wise mentor",
        look="Sixties, weathered, long grey coat with geometric brass "
             "fasteners, an antique diagnostic slate in hand.",
        motivation="Chief geodesic engineer and keeper of the lost "
                   "blueprints, giving Leo the knowledge and the "
                   "overrides at the moments that matter.",
        default_actions=("RIG_POINT_COMMAND",),
        home_anchor="DOME_APEX_CENTER",
        voice_id="VO_SILAS_GRAVE",
        stature_m=1.76,
    ),
    "CHAR_JAX": Character(
        character_id="CHAR_JAX",
        name='Jax "The Spark"',
        archetype="Unhinged disruptor",
        look="Late twenties, asymmetric hair, leather jacket with neon "
             "trim, restless.",
        motivation="Rogue saboteur who threatens the facility itself and "
                   "makes every scene physically dangerous.",
        default_actions=("RIG_INVASIVE_STEP", "RIG_GRAB_LAPEL"),
        home_anchor="DOME_STRUT_TOP",
        voice_id="VO_JAX_UNHINGED",
        stature_m=1.79,
    ),
    "CHAR_BARON": Character(
        character_id="CHAR_BARON",
        name="Baron Vance",
        archetype="Systemic titan",
        look="Fifties, imposing, immaculate dark suit with metallic "
             "dome-strut lapel pins, a cold and unhurried gaze.",
        motivation="Monopolist holding the whole dome network, and the "
                   "obstacle Leo has to beat to save it.",
        default_actions=("RIG_POINT_COMMAND", "RIG_DISDAINFUL_TURN"),
        home_anchor="DOME_CURVED_WALL_SOUTH",
        voice_id="VO_BARON_COLD",
        stature_m=1.88,
    ),
}


# ----------------------------------------------------------------------
# The beat sheet
# ----------------------------------------------------------------------

BEAT_ORDER: tuple[str, ...] = ("COLD_HOOK", "ESCALATION", "REVEAL",
                               "CLIFFHANGER")
HOOK_DEADLINE_S = 8.0
"""The hook has to have landed by here or the viewer is already gone."""

EPISODE_MIN_S = 55.0
EPISODE_MAX_S = 95.0
WORD_BUDGET = 160
"""Spoken words per episode, from the implementation checklist."""

MAX_WORDS_PER_SECOND = 3.0
"""Above this a line is being rushed and the reaction gets clipped."""


@dataclass(frozen=True)
class CameraCue:
    preset: str
    target_character: str
    focal_mm: float
    """The script's ``fov`` field, read as a lens in millimetres."""


@dataclass(frozen=True)
class ActionCue:
    character_id: str
    rig_action: str
    target_id: str | None = None
    distance_m: float | None = None
    spatial_anchor: str | None = None


@dataclass(frozen=True)
class Beat:
    start_s: float
    end_s: float
    dramatic_beat: str
    camera: CameraCue
    actions: tuple[ActionCue, ...]
    dialogue: str
    voice_id: str

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s

    @property
    def words(self) -> int:
        return len(self.dialogue.split())

    @property
    def words_per_second(self) -> float:
        return self.words / max(1e-6, self.duration_s)

    @property
    def cast(self) -> tuple[str, ...]:
        names = [self.camera.target_character]
        for cue in self.actions:
            names.append(cue.character_id)
            if cue.target_id:
                names.append(cue.target_id)
        return tuple(dict.fromkeys(names))


@dataclass(frozen=True)
class Episode:
    episode_id: str
    dome_preset: str
    lighting_theme: str
    structural_lights_intensity: float
    beats: tuple[Beat, ...]
    title: str = ""
    question: str = ""
    """What this episode makes the viewer need to know."""
    answers: str = ""
    """The episode_id whose question this one settles, if any."""

    @property
    def duration_s(self) -> float:
        return self.beats[-1].end_s if self.beats else 0.0

    @property
    def words(self) -> int:
        return sum(beat.words for beat in self.beats)

    @property
    def cast(self) -> tuple[str, ...]:
        names: list[str] = []
        for beat in self.beats:
            names.extend(beat.cast)
        return tuple(dict.fromkeys(names))


def parse_timestamp(value: str | float) -> float:
    """``"1:05"`` or ``65`` to seconds, with a clear error either way."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if ":" not in text:
        return float(text)
    minutes, seconds = text.split(":", 1)
    return float(minutes) * 60.0 + float(seconds)


def parse_episode(payload: dict) -> Episode:
    """Turn the specification's JSON into typed, checked objects."""
    environment = payload.get("environment", {})
    beats: list[Beat] = []
    for index, entry in enumerate(payload.get("sequence", [])):
        camera = entry.get("camera", {})
        audio = entry.get("audio", {})
        actions = tuple(
            ActionCue(
                character_id=cue["character_id"],
                rig_action=cue["rig_action"],
                target_id=cue.get("target_id"),
                distance_m=(float(cue["distance_meters"])
                            if "distance_meters" in cue else None),
                spatial_anchor=cue.get("spatial_anchor"),
            )
            for cue in entry.get("character_actions", [])
        )
        beats.append(Beat(
            start_s=parse_timestamp(entry["timestamp_start"]),
            end_s=parse_timestamp(entry["timestamp_end"]),
            dramatic_beat=entry["dramatic_beat"],
            camera=CameraCue(
                preset=camera.get("preset", "CAM_OTS_VERTICAL"),
                target_character=camera.get("target_character", ""),
                focal_mm=float(camera.get("fov", 50)),
            ),
            actions=actions,
            dialogue=audio.get("dialogue_text", ""),
            voice_id=audio.get("voice_id", ""),
        ))
        if not beats[-1].dialogue:
            raise ValueError(f"beat {index} of {payload.get('episode_id')} "
                             "has no dialogue")
    return Episode(
        title=payload.get("title", ""),
        question=payload.get("question", ""),
        answers=payload.get("answers", ""),
        episode_id=payload["episode_id"],
        dome_preset=environment.get("dome_preset",
                                    "GEODESIC_GARAGE_WORKSHOP"),
        lighting_theme=environment.get("lighting_theme",
                                       "NIGHT_RAIN_CYAN_AMBER"),
        structural_lights_intensity=float(
            environment.get("structural_lights_intensity", 0.8)),
        beats=tuple(beats),
    )


def load_episode(path: str | Path) -> Episode:
    return parse_episode(json.loads(Path(path).read_text(encoding="utf-8")))


# The specification's own example, carried here so the parser and the
# checks below are proved against the published script rather than
# against something written to pass them.
EXAMPLE_EPISODE_JSON: dict = {
    "episode_id": "EP_DOME_001",
    "environment": {
        "dome_preset": "GEODESIC_GARAGE_WORKSHOP",
        "lighting_theme": "NIGHT_RAIN_CYAN_AMBER",
        "structural_lights_intensity": 0.8,
    },
    "sequence": [
        {
            "timestamp_start": "0:00", "timestamp_end": "0:08",
            "dramatic_beat": "COLD_HOOK",
            "camera": {"preset": "CAM_DOLLY_PUSH_FAST",
                       "target_character": "CHAR_AURELIA", "fov": 35},
            "character_actions": [
                {"character_id": "CHAR_AURELIA",
                 "rig_action": "RIG_SLAP_EXECUTE",
                 "target_id": "CHAR_LEO"},
                {"character_id": "CHAR_LEO",
                 "rig_action": "RIG_GASP_REACTION",
                 "target_id": "CHAR_AURELIA"},
            ],
            "audio": {
                "dialogue_text": "How dare you enter the High Council Dome "
                                 "without my permission!",
                "voice_id": "VO_AURELIA_ANGRY"},
        },
        {
            "timestamp_start": "0:08", "timestamp_end": "0:25",
            "dramatic_beat": "ESCALATION",
            "camera": {"preset": "CAM_OTS_VERTICAL",
                       "target_character": "CHAR_LEO", "fov": 50},
            "character_actions": [
                {"character_id": "CHAR_LEO",
                 "rig_action": "RIG_INVASIVE_STEP",
                 "target_id": "CHAR_AURELIA", "distance_meters": 0.5},
                {"character_id": "CHAR_LEO",
                 "rig_action": "RIG_CLENCH_FIST_RAISE"},
            ],
            "audio": {
                "dialogue_text": "I built these structural struts! This "
                                 "entire dome falls apart without my key!",
                "voice_id": "VO_LEO_DEFIANT"},
        },
        {
            "timestamp_start": "0:25", "timestamp_end": "0:45",
            "dramatic_beat": "REVEAL",
            "camera": {"preset": "CAM_LOW_ANGLE_TILT",
                       "target_character": "CHAR_SILAS", "fov": 28},
            "character_actions": [
                {"character_id": "CHAR_SILAS",
                 "spatial_anchor": "DOME_APEX_CENTER",
                 "rig_action": "RIG_POINT_COMMAND",
                 "target_id": "CHAR_AURELIA"},
            ],
            "audio": {
                "dialogue_text": "He speaks the truth, Aurelia. He is the "
                                 "rightful master of the Vance Network.",
                "voice_id": "VO_SILAS_GRAVE"},
        },
        {
            "timestamp_start": "0:45", "timestamp_end": "1:00",
            "dramatic_beat": "CLIFFHANGER",
            "camera": {"preset": "CAM_WHIP_PAN",
                       "target_character": "CHAR_JAX", "fov": 40},
            "character_actions": [
                {"character_id": "CHAR_JAX",
                 "spatial_anchor": "DOME_SCORD_STRUT_TOP",
                 "rig_action": "RIG_INVASIVE_STEP",
                 "target_id": "CHAR_SILAS"},
            ],
            "audio": {
                "dialogue_text": "Too late, old man! The explosive charges "
                                 "are already armed across the outer facets!",
                "voice_id": "VO_JAX_UNHINGED"},
        },
    ],
}


def example_episode() -> Episode:
    return parse_episode(EXAMPLE_EPISODE_JSON)


# ----------------------------------------------------------------------
# The mini-series
# ----------------------------------------------------------------------

SERIES_TITLE = "THE VANCE NETWORK"
SERIES_LOGLINE = (
    "A disgraced dome mechanic is the rightful heir to the network of "
    "shells he maintains, and the only person who can keep the one over "
    "everybody's head from coming down."
)


def _beat(start, end, name, preset, target, focal, actions, line, voice):
    return {
        "timestamp_start": start, "timestamp_end": end,
        "dramatic_beat": name,
        "camera": {"preset": preset, "target_character": target,
                   "fov": focal},
        "character_actions": actions,
        "audio": {"dialogue_text": line, "voice_id": voice},
    }


def _act(character, action, target=None, anchor=None, distance=None):
    cue = {"character_id": character, "rig_action": action}
    if target:
        cue["target_id"] = target
    if anchor:
        cue["spatial_anchor"] = anchor
    if distance is not None:
        cue["distance_meters"] = distance
    return cue


EPISODE_002 = {
    "episode_id": "EP_DOME_002",
    "title": "The Charges",
    "answers": "EP_DOME_001",
    "question": "Will the shell hold once Leo re-routes the load?",
    "environment": {"dome_preset": "GEODESIC_GARAGE_WORKSHOP",
                    "lighting_theme": "NIGHT_RAIN_CYAN_AMBER",
                    "structural_lights_intensity": 0.55},
    "sequence": [
        _beat("0:00", "0:08", "COLD_HOOK", "CAM_DOLLY_PUSH_FAST",
              "CHAR_JAX", 35,
              [_act("CHAR_LEO", "RIG_GRAB_LAPEL", "CHAR_JAX"),
               _act("CHAR_JAX", "RIG_INVASIVE_STEP", "CHAR_LEO")],
              "Cut the power and they blow. Cut me and they blow. Choose.",
              "VO_JAX_UNHINGED"),
        _beat("0:08", "0:26", "ESCALATION", "CAM_OTS_VERTICAL",
              "CHAR_LEO", 50,
              [_act("CHAR_LEO", "RIG_CLENCH_FIST_RAISE", "CHAR_JAX"),
               _act("CHAR_LEO", "RIG_INVASIVE_STEP", "CHAR_JAX",
                    distance=0.5)],
              "Then I do neither. I re-route the whole load through the "
              "base ring.",
              "VO_LEO_DEFIANT"),
        _beat("0:26", "0:46", "REVEAL", "CAM_LOW_ANGLE_TILT",
              "CHAR_SILAS", 28,
              [_act("CHAR_SILAS", "RIG_POINT_COMMAND", "CHAR_LEO",
                    anchor="DOME_APEX_CENTER")],
              "The base ring was never rated for that. He is gambling "
              "with the whole shell.",
              "VO_SILAS_GRAVE"),
        _beat("0:46", "1:02", "CLIFFHANGER", "CAM_WHIP_PAN",
              "CHAR_AURELIA", 40,
              [_act("CHAR_AURELIA", "RIG_DISDAINFUL_TURN", "CHAR_LEO")],
              "My father is watching. If it cracks, the Network takes "
              "this dome back tonight.",
              "VO_AURELIA_ANGRY"),
    ],
}

EPISODE_003 = {
    "episode_id": "EP_DOME_003",
    "title": "The Base Ring",
    "answers": "EP_DOME_002",
    "question": "Do the original blueprints survive the night?",
    "environment": {"dome_preset": "GEODESIC_GARAGE_WORKSHOP",
                    "lighting_theme": "NIGHT_RAIN_CYAN_AMBER",
                    "structural_lights_intensity": 0.9},
    "sequence": [
        _beat("0:00", "0:08", "COLD_HOOK", "CAM_DOLLY_PUSH_FAST",
              "CHAR_AURELIA", 35,
              [_act("CHAR_AURELIA", "RIG_GASP_REACTION", "CHAR_LEO")],
              "It held. Every strut he touched is standing, and the "
              "Council saw it hold.",
              "VO_AURELIA_ANGRY"),
        _beat("0:08", "0:28", "ESCALATION", "CAM_OTS_VERTICAL",
              "CHAR_BARON", 50,
              [_act("CHAR_BARON", "RIG_INVASIVE_STEP", "CHAR_LEO",
                    distance=0.45),
               _act("CHAR_BARON", "RIG_POINT_COMMAND", "CHAR_LEO")],
              "A mechanic who saves a dome is still a mechanic. Sign "
              "the release.",
              "VO_BARON_COLD"),
        _beat("0:28", "0:48", "REVEAL", "CAM_LOW_ANGLE_TILT",
              "CHAR_SILAS", 28,
              [_act("CHAR_SILAS", "RIG_POINT_COMMAND", "CHAR_BARON",
                    anchor="DOME_APEX_CENTER")],
              "He signs nothing. The original blueprints name him, and "
              "I kept them.",
              "VO_SILAS_GRAVE"),
        _beat("0:48", "1:04", "CLIFFHANGER", "CAM_WHIP_PAN",
              "CHAR_JAX", 40,
              [_act("CHAR_JAX", "RIG_INVASIVE_STEP", "CHAR_SILAS",
                    anchor="DOME_STRUT_TOP")],
              "Paper burns, old man. Ask me how I know that.",
              "VO_JAX_UNHINGED"),
    ],
}

EPISODE_004 = {
    "episode_id": "EP_DOME_004",
    "title": "The Originals",
    "answers": "EP_DOME_003",
    "question": "Which way does the Council vote?",
    "environment": {"dome_preset": "GEODESIC_COUNCIL_HALL",
                    "lighting_theme": "COLD_WHITE_APEX_SHAFT",
                    "structural_lights_intensity": 0.35},
    "sequence": [
        _beat("0:00", "0:08", "COLD_HOOK", "CAM_DOLLY_PUSH_FAST",
              "CHAR_JAX", 35,
              [_act("CHAR_JAX", "RIG_INVASIVE_STEP", "CHAR_AURELIA",
                    distance=0.5)],
              "Twelve rolls of vellum. One match. Say the word, heiress.",
              "VO_JAX_UNHINGED"),
        _beat("0:08", "0:26", "ESCALATION", "CAM_OTS_VERTICAL",
              "CHAR_AURELIA", 50,
              [_act("CHAR_AURELIA", "RIG_SLAP_EXECUTE", "CHAR_JAX"),
               _act("CHAR_JAX", "RIG_GASP_REACTION", "CHAR_AURELIA")],
              "The word is no. And you were never the one holding the "
              "match.",
              "VO_AURELIA_ANGRY"),
        _beat("0:26", "0:46", "REVEAL", "CAM_LOW_ANGLE_TILT",
              "CHAR_SILAS", 28,
              [_act("CHAR_SILAS", "RIG_POINT_COMMAND", "CHAR_AURELIA",
                    anchor="DOME_APEX_CENTER")],
              "She copied every sheet the night the Council sealed the "
              "vault.",
              "VO_SILAS_GRAVE"),
        _beat("0:46", "1:02", "CLIFFHANGER", "CAM_WHIP_PAN",
              "CHAR_BARON", 40,
              [_act("CHAR_BARON", "RIG_DISDAINFUL_TURN", "CHAR_AURELIA")],
              "Then we do this the old way. Convene the vote. Tonight.",
              "VO_BARON_COLD"),
    ],
}

EPISODE_005 = {
    "episode_id": "EP_DOME_005",
    "title": "The Vote",
    "answers": "EP_DOME_004",
    "question": "What does putting her name behind him cost Aurelia?",
    "environment": {"dome_preset": "GEODESIC_COUNCIL_HALL",
                    "lighting_theme": "COLD_WHITE_APEX_SHAFT",
                    "structural_lights_intensity": 0.5},
    "sequence": [
        _beat("0:00", "0:08", "COLD_HOOK", "CAM_DOLLY_PUSH_FAST",
              "CHAR_BARON", 35,
              [_act("CHAR_BARON", "RIG_POINT_COMMAND", "CHAR_SILAS",
                    anchor="DOME_APEX_CENTER")],
              "Ninety per cent of this Network answers to me. Count it "
              "and be done.",
              "VO_BARON_COLD"),
        _beat("0:08", "0:28", "ESCALATION", "CAM_OTS_VERTICAL",
              "CHAR_LEO", 50,
              [_act("CHAR_LEO", "RIG_INVASIVE_STEP", "CHAR_BARON",
                    distance=0.5),
               _act("CHAR_LEO", "RIG_CLENCH_FIST_RAISE", "CHAR_BARON")],
              "Count the domes instead. Forty of them went up under my "
              "hands.",
              "VO_LEO_DEFIANT"),
        _beat("0:28", "0:48", "REVEAL", "CAM_LOW_ANGLE_TILT",
              "CHAR_SILAS", 28,
              [_act("CHAR_SILAS", "RIG_POINT_COMMAND", "CHAR_BARON",
                    anchor="DOME_APEX_CENTER")],
              "The charter counts builders, Vance. It always did. Read "
              "clause nine.",
              "VO_SILAS_GRAVE"),
        _beat("0:48", "1:04", "CLIFFHANGER", "CAM_WHIP_PAN",
              "CHAR_AURELIA", 40,
              [_act("CHAR_AURELIA", "RIG_GASP_REACTION", "CHAR_BARON")],
              "Then he does not need your name. He already has mine.",
              "VO_AURELIA_ANGRY"),
    ],
}

EPISODE_006 = {
    "episode_id": "EP_DOME_006",
    "title": "The Name",
    "answers": "EP_DOME_005",
    "question": "Where is the second set of charges?",
    "environment": {"dome_preset": "GEODESIC_COUNCIL_HALL",
                    "lighting_theme": "COLD_WHITE_APEX_SHAFT",
                    "structural_lights_intensity": 0.75},
    "sequence": [
        _beat("0:00", "0:08", "COLD_HOOK", "CAM_DOLLY_PUSH_FAST",
              "CHAR_BARON", 35,
              [_act("CHAR_BARON", "RIG_DISDAINFUL_TURN", "CHAR_AURELIA")],
              "You gave a mechanic your name. You gave away the whole "
              "Network.",
              "VO_BARON_COLD"),
        _beat("0:08", "0:26", "ESCALATION", "CAM_OTS_VERTICAL",
              "CHAR_AURELIA", 50,
              [_act("CHAR_AURELIA", "RIG_INVASIVE_STEP", "CHAR_BARON",
                    distance=0.45)],
              "I gave it to the only person here who ever fixed "
              "anything.",
              "VO_AURELIA_ANGRY"),
        _beat("0:26", "0:48", "REVEAL", "CAM_LOW_ANGLE_TILT",
              "CHAR_LEO", 28,
              [_act("CHAR_LEO", "RIG_POINT_COMMAND", "CHAR_BARON",
                    anchor="DOME_APEX_CENTER")],
              "The Network is not a name. It is sixty-five struts and "
              "everyone who cut them.",
              "VO_LEO_DEFIANT"),
        _beat("0:48", "1:04", "CLIFFHANGER", "CAM_WHIP_PAN",
              "CHAR_JAX", 40,
              [_act("CHAR_JAX", "RIG_INVASIVE_STEP", "CHAR_LEO",
                    anchor="DOME_STRUT_TOP")],
              "Beautiful speech. Shame about the second set of charges.",
              "VO_JAX_UNHINGED"),
    ],
}

EPISODE_001 = dict(
    EXAMPLE_EPISODE_JSON,
    title="The High Council Dome",
    question="Who armed the charges across the outer facets?",
)

SERIES_JSON: tuple[dict, ...] = (
    EPISODE_001, EPISODE_002, EPISODE_003, EPISODE_004, EPISODE_005,
    EPISODE_006,
)


def series() -> tuple[Episode, ...]:
    """Every episode of the mini-series, parsed and in order."""
    return tuple(parse_episode(payload) for payload in SERIES_JSON)


def check_series(episodes: tuple[Episode, ...] | None = None
                 ) -> tuple[str, ...]:
    """Everything wrong with the series as a series, not episode by episode.

    A mini-series fails in ways a single episode cannot: an unanswered
    question, a cliffhanger nobody picks up, a character who vanishes, a
    finale that resolves everything and leaves nothing to come back for.
    """
    episodes = series() if episodes is None else episodes
    problems: list[str] = []
    if not episodes:
        return ("the series has no episodes",)

    identifiers = [episode.episode_id for episode in episodes]
    if len(set(identifiers)) != len(identifiers):
        problems.append("two episodes share an id")

    for episode in episodes:
        problems.extend(f"{episode.episode_id}: {problem}"
                        for problem in check_episode(episode))
        if not episode.title:
            problems.append(f"{episode.episode_id} has no title")
        if not episode.question:
            problems.append(f"{episode.episode_id} asks nothing")

    answered = {episode.answers for episode in episodes if episode.answers}
    for index, episode in enumerate(episodes[:-1]):
        if episode.episode_id not in answered:
            problems.append(
                f"{episode.episode_id} asks a question no later episode "
                "answers")
        following = episodes[index + 1]
        if following.answers and following.answers != episode.episode_id:
            problems.append(
                f"{following.episode_id} answers "
                f"{following.answers}, not the episode before it")
        # The cliffhanger has to be picked up: somebody in it must be in
        # the next episode's hook, or the cut between them is a reset.
        cliff = episode.beats[-1].cast
        hook = following.beats[0].cast
        if not set(cliff) & set(hook):
            problems.append(
                f"nobody from {episode.episode_id}'s cliffhanger appears "
                f"in {following.episode_id}'s hook")

    if episodes[-1].episode_id in answered:
        problems.append("the finale is answered inside its own series")
    if not episodes[-1].question:
        problems.append("the finale leaves nothing open")

    # A series that drops a character has wasted an archetype.
    seen: set[str] = set()
    for episode in episodes:
        seen.update(episode.cast)
    missing = set(CAST) - seen
    if missing:
        problems.append(
            f"never cast: {', '.join(sorted(missing))}")
    return tuple(problems)


def series_bible() -> str:
    """The series as a writer would read it: arc first, then the beats."""
    episodes = series()
    lines = [
        SERIES_TITLE,
        "",
        SERIES_LOGLINE,
        "",
        f"{len(episodes)} episodes, "
        f"{sum(episode.duration_s for episode in episodes) / 60.0:.1f} "
        f"minutes, {sum(episode.words for episode in episodes)} spoken "
        "words.",
        "",
        "THE ARC",
        "",
    ]
    for episode in episodes:
        answers = (f" (answers {episode.answers})" if episode.answers
                   else "")
        lines.append(f"  {episode.episode_id}  {episode.title}{answers}")
        lines.append(f"      asks: {episode.question}")
        lines.append(f"      {episode.duration_s:.0f}s, "
                     f"{episode.words} words, cast "
                     f"{', '.join(CAST[name].name for name in episode.cast)}")
        lines.append("")
    lines.append("=" * 68)
    lines.append("")
    for episode in episodes:
        lines.append(beat_sheet(episode))
    return "\n".join(lines)


def check_episode(episode: Episode) -> tuple[str, ...]:
    """Every reason this episode could not be shot, in one list.

    Returns the problems rather than raising on the first, because a
    writer fixing a script wants the whole list.
    """
    problems: list[str] = []
    anchors = stage_anchors()

    if episode.dome_preset not in DOME_PRESETS:
        problems.append(f"unknown dome preset {episode.dome_preset!r}")
    if not episode.beats:
        problems.append("episode has no beats")
        return tuple(problems)

    if abs(episode.beats[0].start_s) > 1e-9:
        problems.append("the first beat does not start at zero")
    for earlier, later in zip(episode.beats, episode.beats[1:]):
        if abs(earlier.end_s - later.start_s) > 1e-6:
            problems.append(
                f"gap or overlap between {earlier.dramatic_beat} and "
                f"{later.dramatic_beat} at {earlier.end_s:g}s")
    if not EPISODE_MIN_S <= episode.duration_s <= EPISODE_MAX_S:
        problems.append(
            f"episode runs {episode.duration_s:g}s, outside the "
            f"{EPISODE_MIN_S:g}-{EPISODE_MAX_S:g}s window")

    named = [beat.dramatic_beat for beat in episode.beats]
    for expected in BEAT_ORDER:
        if expected not in named:
            problems.append(f"no {expected} beat")
    if named != sorted(named, key=lambda name: BEAT_ORDER.index(name)
                       if name in BEAT_ORDER else len(BEAT_ORDER)):
        problems.append("beats are out of the hook-escalation-reveal-"
                        "cliffhanger order")
    hook = next((beat for beat in episode.beats
                 if beat.dramatic_beat == "COLD_HOOK"), None)
    if hook is not None and hook.end_s > HOOK_DEADLINE_S + 1e-9:
        problems.append(
            f"the hook runs to {hook.end_s:g}s, past the "
            f"{HOOK_DEADLINE_S:g}s deadline")

    if episode.words > WORD_BUDGET:
        problems.append(
            f"{episode.words} spoken words, over the {WORD_BUDGET} budget")

    for beat in episode.beats:
        if beat.duration_s <= 0.0:
            problems.append(f"{beat.dramatic_beat} has no duration")
        if beat.words_per_second > MAX_WORDS_PER_SECOND:
            problems.append(
                f"{beat.dramatic_beat} needs "
                f"{beat.words_per_second:.2f} words a second, over "
                f"{MAX_WORDS_PER_SECOND:g}")
        if beat.camera.preset not in SHOTS:
            problems.append(f"unknown camera preset {beat.camera.preset!r}")
        if beat.camera.target_character not in CAST:
            problems.append(
                f"camera targets unknown character "
                f"{beat.camera.target_character!r}")
        if not 8.0 <= beat.camera.focal_mm <= 300.0:
            problems.append(
                f"{beat.camera.focal_mm:g} is not a plausible lens in mm")
        if not beat.voice_id:
            problems.append(f"{beat.dramatic_beat} has no voice id")
        for cue in beat.actions:
            if cue.character_id not in CAST:
                problems.append(f"unknown character {cue.character_id!r}")
            if cue.rig_action not in ACTIONS:
                problems.append(f"unknown rig action {cue.rig_action!r}")
            if cue.target_id is not None and cue.target_id not in CAST:
                problems.append(f"unknown target {cue.target_id!r}")
            if (cue.spatial_anchor is not None
                    and cue.spatial_anchor not in anchors):
                problems.append(f"unknown anchor {cue.spatial_anchor!r}")
            if cue.distance_m is not None and not 0.2 <= cue.distance_m <= 4.0:
                problems.append(
                    f"{cue.distance_m:g} m is not a staging distance")
    return tuple(problems)


def beat_sheet(episode: Episode) -> str:
    """The episode as a readable beat sheet, for the audit report."""
    lines = [
        f"EPISODE {episode.episode_id}",
        f"  set        {episode.dome_preset} / {episode.lighting_theme} "
        f"at {episode.structural_lights_intensity:.2f}",
        f"  runtime    {episode.duration_s:.0f}s in {len(episode.beats)} "
        "beats",
        f"  dialogue   {episode.words} words of {WORD_BUDGET} "
        f"({episode.words / max(1e-6, episode.duration_s):.2f} a second "
        "overall)",
        f"  cast       {', '.join(CAST[name].name for name in episode.cast)}",
        "",
    ]
    for beat in episode.beats:
        lines.append(
            f"  {beat.start_s:5.1f}-{beat.end_s:5.1f}s  "
            f"{beat.dramatic_beat:<12} {beat.camera.preset} on "
            f"{CAST[beat.camera.target_character].name} "
            f"({beat.camera.focal_mm:g} mm)")
        for cue in beat.actions:
            target = f" -> {CAST[cue.target_id].name}" if cue.target_id else ""
            anchor = f" @ {cue.spatial_anchor}" if cue.spatial_anchor else ""
            spacing = (f" at {cue.distance_m:g} m"
                       if cue.distance_m is not None else "")
            lines.append(f"        {CAST[cue.character_id].name}: "
                         f"{cue.rig_action}{target}{anchor}{spacing}")
        lines.append(f'        "{beat.dialogue}"')
        lines.append(f"        {beat.words} words, "
                     f"{beat.words_per_second:.2f} a second, "
                     f"{beat.voice_id}")
        lines.append("")
    return "\n".join(lines)


def validate_drama_script() -> None:
    """Prove the schema, the cast, and the specification's own episode."""
    for character_id, character in CAST.items():
        assert character.character_id == character_id
        assert character.look.endswith("."), character_id
        assert character.motivation.endswith("."), character_id
        assert character.default_actions, character_id
        for action in character.default_actions:
            assert action in ACTIONS, (character_id, action)
        assert character.home_anchor in stage_anchors(), character_id
        assert 1.4 < character.stature_m < 2.1, character_id
    assert len(CAST) == 5, "the specification defines five archetypes"

    assert parse_timestamp("1:05") == 65.0
    assert parse_timestamp("0:08") == 8.0
    assert parse_timestamp(12) == 12.0

    episode = example_episode()
    assert episode.episode_id == "EP_DOME_001"
    assert len(episode.beats) == 4
    assert episode.duration_s == 60.0
    assert [beat.dramatic_beat for beat in episode.beats] == list(BEAT_ORDER)
    assert episode.words <= WORD_BUDGET, episode.words

    problems = check_episode(episode)
    assert not problems, problems

    # The checks have to actually bite, or they are decoration.  Each
    # of these is a real way a script goes wrong.
    from dataclasses import replace as _replace

    gapped = _replace(episode, beats=(
        episode.beats[0],
        _replace(episode.beats[1], start_s=10.0),
    ) + episode.beats[2:])
    assert any("gap or overlap" in problem for problem in
               check_episode(gapped))

    rushed = _replace(episode, beats=(
        _replace(episode.beats[0], dialogue=" ".join(["word"] * 40)),
    ) + episode.beats[1:])
    assert any("words a second" in problem for problem in
               check_episode(rushed))

    wordy = _replace(episode, beats=tuple(
        _replace(beat, dialogue=" ".join(["word"] * 50))
        for beat in episode.beats))
    assert any("over the 160" in problem for problem in check_episode(wordy))

    unknown = _replace(episode, beats=(
        _replace(episode.beats[0], camera=_replace(
            episode.beats[0].camera, preset="CAM_NOPE")),
    ) + episode.beats[1:])
    assert any("unknown camera preset" in problem for problem in
               check_episode(unknown))

    late_hook = _replace(episode, beats=(
        _replace(episode.beats[0], end_s=12.0),
        _replace(episode.beats[1], start_s=12.0),
    ) + episode.beats[2:])
    assert any("past the 8s deadline" in problem for problem in
               check_episode(late_hook))

    sheet = beat_sheet(episode)
    assert "EP_DOME_001" in sheet and "COLD_HOOK" in sheet

    # The mini-series, as a series.
    episodes = series()
    assert len(episodes) == 6, len(episodes)
    problems = check_series(episodes)
    assert not problems, problems

    # Every archetype earns its place, including the one the first
    # episode never uses.
    cast_seen = set()
    for item in episodes:
        cast_seen.update(item.cast)
    assert cast_seen == set(CAST), sorted(set(CAST) - cast_seen)

    # The chain of questions really is a chain: each episode answers the
    # one before it and the finale leaves exactly one thread hanging.
    for earlier, later in zip(episodes, episodes[1:]):
        assert later.answers == earlier.episode_id, (earlier.episode_id,
                                                     later.answers)
    open_threads = [item for item in episodes
                    if item.episode_id not in {other.answers
                                               for other in episodes}]
    assert [item.episode_id for item in open_threads] == \
        [episodes[-1].episode_id]

    # The series checks have to bite, or they are decoration.
    from dataclasses import replace as _swap
    broken = list(episodes)
    broken[2] = _swap(broken[2], answers="EP_DOME_001")
    assert any("not the episode before it" in problem
               for problem in check_series(tuple(broken)))
    resolved = list(episodes)
    resolved[-1] = _swap(resolved[-1], question="")
    assert any("leaves nothing open" in problem
               for problem in check_series(tuple(resolved)))

    bible = series_bible()
    assert SERIES_TITLE in bible and "EP_DOME_006" in bible
