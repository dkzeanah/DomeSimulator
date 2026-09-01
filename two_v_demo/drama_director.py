"""The Drama Director Controller: a script becomes a timed state stream.

This is the piece the specification puts at the top of the diagram.  It
takes a parsed :class:`~two_v_demo.drama_script.Episode` and answers one
question for any instant of it: *where is everybody, what are they
doing, and where is the camera?*

Everything downstream -- the renderer, a still, an exported frame -- asks
:meth:`Director.state_at` and draws what it gets back.  Nothing in this
module touches OpenGL, so the whole timeline can be checked, measured
and argued with before a single frame is drawn.

Blocking is resolved rather than authored.  A beat says "Leo steps to
half a metre of Aurelia"; this module turns that into two floor
positions, two facings, and the ring the pair end up in -- and complains
if the result would put them somewhere the specification's proximity
rules say they should not be.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .drama_camera import (
    CameraState,
    cam_dolly_push_fast,
    cam_low_angle_tilt,
    cam_ots_vertical,
    cam_whip_pan,
)
from .drama_rig import (
    ACTIONS,
    PERSONAL_RING,
    RigState,
    centre_distance_for_gap,
    execute,
    eye_contact_yaw,
    eye_line,
    facing_yaw,
    gap_for_centre_distance,
    posed_joints,
    ring_for,
    stand_off,
)
from .drama_script import CAST, Beat, Episode, example_episode
from .drama_stage import (
    DOME_PRESETS,
    apex_light,
    key_light_direction,
    rim_lights,
    stage_anchors,
)


CUE_LEAD_S = 0.30
"""How long after a beat opens the first action fires.  Long enough for
the cut to land, short enough that the beat is not dead air."""

CUE_STAGGER_S = 0.45
"""Between one character's action and the next character's answer: the
gasp arrives just after the slap connects, not with it."""

CONTACT_SPACING_M = 0.45
"""Inside the confrontation ring: where a slap or a grab can land."""

DEFAULT_SPACING_M = 0.90
"""Where two characters stand when the script does not say: the middle
of the personal ring."""


@dataclass(frozen=True)
class CharacterState:
    """One character at one instant."""

    character_id: str
    spot: np.ndarray
    facing_deg: float
    rig: RigState
    joints: dict
    ring: str
    """Which proximity ring this character is in with the beat's other."""
    attached_to: tuple[str, str] | None = None
    """``(other character, socket)`` while a grab is holding."""

    @property
    def eye(self) -> np.ndarray:
        return eye_line(self.joints)


@dataclass(frozen=True)
class DirectorState:
    """The whole stage at one instant, ready to draw."""

    time_s: float
    beat: Beat
    beat_progress: float
    camera: CameraState
    characters: dict
    dome_radius_m: float
    lighting_theme: str
    key_light: np.ndarray
    apex_light: np.ndarray
    rim_light_intensity: float
    dialogue: str


@dataclass
class _Blocking:
    """Where a beat puts everyone, worked out once per beat."""

    spots: dict = field(default_factory=dict)
    facings: dict = field(default_factory=dict)
    spacing_m: float = DEFAULT_SPACING_M
    pair: tuple = ()


class Director:
    """Plays one episode: ``state_at(t)`` for any instant in it."""

    def __init__(self, episode: Episode | None = None) -> None:
        self.episode = episode or example_episode()
        preset = DOME_PRESETS[self.episode.dome_preset]
        self.dome_radius_m = preset.radius_m
        self.anchors = stage_anchors(preset.radius_m)
        self.rim_lights = rim_lights(
            preset.radius_m, self.episode.structural_lights_intensity)
        self.blocking = tuple(self._block(beat) for beat in self.episode.beats)

    # ------------------------------------------------------------------
    # Blocking
    # ------------------------------------------------------------------

    def _anchor_spot(self, character_id: str, beat: Beat) -> np.ndarray:
        """Where a character stands before any step is applied."""
        for cue in beat.actions:
            if cue.character_id == character_id and cue.spatial_anchor:
                anchor = self.anchors[cue.spatial_anchor]
                return np.array([anchor.position[0], anchor.position[1],
                                 anchor.height_m])
        anchor = self.anchors[CAST[character_id].home_anchor]
        return np.array([anchor.position[0], anchor.position[1],
                         anchor.height_m])

    def _block(self, beat: Beat) -> _Blocking:
        """Resolve one beat's floor plan.

        The camera's subject is placed first, because the shot is built
        around them; everyone else is placed relative to that.
        """
        blocking = _Blocking()
        cast = list(beat.cast)
        lead = beat.camera.target_character
        if lead in cast:
            cast.remove(lead)
            cast.insert(0, lead)

        # A beat that contains a slap or a grab is staged in the
        # confrontation ring, because an arm does not reach across the
        # personal ring.  An explicit distance in the script still wins.
        if any(ACTIONS[cue.rig_action].contact for cue in beat.actions):
            blocking.spacing_m = CONTACT_SPACING_M
        for cue in beat.actions:
            if cue.distance_m is not None:
                blocking.spacing_m = cue.distance_m

        for index, character_id in enumerate(cast):
            spot = self._anchor_spot(character_id, beat)
            if index > 0:
                # Stand the answering character at the beat's spacing
                # from the lead, on the line between their anchors.
                lead_spot = blocking.spots[cast[0]]
                # The script's spacing is the gap between two people,
                # so the floor positions are a body further apart.
                centres = centre_distance_for_gap(blocking.spacing_m)
                if float(np.linalg.norm((spot - lead_spot)[:2])) < 1e-6:
                    spot = lead_spot + np.array([centres, 0.0, 0.0])
                else:
                    placed = stand_off(lead_spot, spot, centres)
                    spot = np.array([placed[0], placed[1], spot[2]])
            blocking.spots[character_id] = spot

        for character_id in cast:
            others = [name for name in cast if name != character_id]
            if others:
                blocking.facings[character_id] = facing_yaw(
                    blocking.spots[character_id], blocking.spots[others[0]])
            else:
                blocking.facings[character_id] = facing_yaw(
                    blocking.spots[character_id], np.zeros(3))
        blocking.pair = tuple(cast[:2])
        return blocking

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------

    def beat_at(self, time_s: float) -> tuple[int, Beat]:
        for index, beat in enumerate(self.episode.beats):
            if beat.start_s <= time_s < beat.end_s:
                return index, beat
        last = len(self.episode.beats) - 1
        return last, self.episode.beats[last]

    def cue_start(self, beat: Beat, cue_index: int) -> float:
        return beat.start_s + CUE_LEAD_S + cue_index * CUE_STAGGER_S

    def _rig_for(self, character_id: str, beat: Beat,
                 time_s: float) -> RigState:
        """The character's latest action, and how far into it we are."""
        latest: RigState | None = None
        for index, cue in enumerate(beat.actions):
            if cue.character_id != character_id:
                continue
            started = self.cue_start(beat, index)
            if time_s + 1e-9 < started:
                continue
            latest = execute(cue.rig_action, time_s - started)
        return latest if latest is not None else execute(None, 0.0)

    def state_at(self, time_s: float) -> DirectorState:
        """Everything the renderer needs for one instant."""
        index, beat = self.beat_at(time_s)
        blocking = self.blocking[index]
        preset = DOME_PRESETS[self.episode.dome_preset]

        characters: dict[str, CharacterState] = {}
        for character_id in blocking.spots:
            rig = self._rig_for(character_id, beat, time_s)
            spot = blocking.spots[character_id]
            facing = blocking.facings[character_id]
            joints = posed_joints(rig, spot, facing,
                                  CAST[character_id].stature_m)
            characters[character_id] = CharacterState(
                character_id=character_id,
                spot=spot,
                facing_deg=facing,
                rig=rig,
                joints=joints,
                ring="distant",
            )

        # Eye contact and the proximity ring need both figures placed,
        # so they are a second pass over the same beat.
        if len(blocking.pair) == 2:
            first, second = blocking.pair
            gap = gap_for_centre_distance(float(np.linalg.norm(
                (characters[first].spot - characters[second].spot)[:2])))
            ring = ring_for(gap)
            for one, other in ((first, second), (second, first)):
                turn = eye_contact_yaw(characters[one].joints,
                                       characters[other].eye,
                                       characters[one].facing_deg)
                state = characters[one]
                # A character who has deliberately turned away keeps
                # their back to the other: eye contact never overrides
                # the disdainful turn.
                if state.rig.action_id == "RIG_DISDAINFUL_TURN":
                    turn = 0.0
                characters[one] = CharacterState(
                    character_id=state.character_id,
                    spot=state.spot,
                    facing_deg=state.facing_deg + turn * 0.5,
                    rig=state.rig,
                    joints=posed_joints(state.rig, state.spot,
                                        state.facing_deg + turn * 0.5,
                                        CAST[one].stature_m),
                    ring=ring,
                    attached_to=self._attachment(one, beat),
                )

        camera = self._camera(beat, characters, time_s)
        return DirectorState(
            time_s=time_s,
            beat=beat,
            beat_progress=((time_s - beat.start_s)
                           / max(1e-6, beat.duration_s)),
            camera=camera,
            characters=characters,
            dome_radius_m=self.dome_radius_m,
            lighting_theme=self.episode.lighting_theme,
            key_light=key_light_direction(self.episode.lighting_theme),
            apex_light=apex_light(self.dome_radius_m),
            rim_light_intensity=preset.structural_lights_intensity,
            dialogue=beat.dialogue,
        )

    OFF_AXIS_DEG = 38.0
    """How far off the eye-line a front-on shot is swung.

    Straight down the eye-line is exactly where the other character is
    standing, so a push-in taken there dollies through their head.  A
    three-quarter angle keeps both faces available and the lens in
    empty air."""

    def _clear_approach(self, subject, others) -> np.ndarray:
        """A direction to shoot the subject from that nobody occupies."""
        facing = math.radians(subject.facing_deg)
        straight = np.array([math.cos(facing), math.sin(facing), 0.0])
        if not others:
            return straight
        blocked = others[0].spot - subject.spot
        best = straight
        clearest = -2.0
        for sign in (1.0, -1.0):
            angle = facing + math.radians(self.OFF_AXIS_DEG) * sign
            candidate = np.array([math.cos(angle), math.sin(angle), 0.0])
            # Prefer the side that points furthest away from whoever
            # else is on the floor.
            clearance = -float(np.dot(candidate[:2],
                                      blocked[:2] / max(1e-6, float(
                                          np.linalg.norm(blocked[:2])))))
            if clearance > clearest:
                clearest, best = clearance, candidate
        return best

    def _attachment(self, character_id: str,
                    beat: Beat) -> tuple[str, str] | None:
        for cue in beat.actions:
            if cue.character_id != character_id:
                continue
            action = ACTIONS[cue.rig_action]
            if action.attach and cue.target_id:
                return (cue.target_id, action.attach)
        return None

    def _camera(self, beat: Beat, characters: dict,
                time_s: float) -> CameraState:
        """The shot for this beat, at this instant."""
        subject_id = beat.camera.target_character
        subject = characters.get(subject_id) or next(iter(characters.values()))
        subject_eye = subject.eye
        # The move starts when the beat's first action does, so a push-in
        # lands on the slap rather than on the cut.
        move_start = self.cue_start(beat, 0)
        elapsed = max(0.0, time_s - move_start)

        others = [state for name, state in characters.items()
                  if name != subject.character_id]
        approach = self._clear_approach(subject, others)

        preset = beat.camera.preset
        if preset == "CAM_DOLLY_PUSH_FAST":
            return cam_dolly_push_fast(subject_eye, approach, elapsed,
                                       focal_start_mm=beat.camera.focal_mm)
        if preset == "CAM_OTS_VERTICAL":
            near = others[0] if others else subject
            return cam_ots_vertical(near.joints, subject_eye,
                                    focal_mm=beat.camera.focal_mm)
        if preset == "CAM_LOW_ANGLE_TILT":
            return cam_low_angle_tilt(subject_eye, approach,
                                      focal_mm=beat.camera.focal_mm)
        if preset == "CAM_WHIP_PAN":
            other = others[0] if others else subject
            pivot = (subject_eye + other.eye) * 0.5 \
                + np.array([0.0, 0.0, 0.0])
            pivot = pivot + np.array([1.6, 0.0, 0.0])
            return cam_whip_pan(pivot, other.eye, subject_eye, elapsed,
                                focal_mm=beat.camera.focal_mm)
        raise ValueError(f"unknown camera preset {preset!r}")

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def frames(self, fps: int = 30):
        """Every frame of the episode, in order."""
        total = int(round(self.episode.duration_s * fps))
        for index in range(total):
            yield self.state_at(index / fps)


def director_report(episode: Episode | None = None) -> str:
    """What the director will actually do, second by second."""
    from .drama_script import beat_sheet

    director = Director(episode)
    lines = [beat_sheet(director.episode), "", "DIRECTOR PLAN", ""]
    for index, beat in enumerate(director.episode.beats):
        blocking = director.blocking[index]
        lines.append(f"  {beat.dramatic_beat} ({beat.start_s:g}-"
                     f"{beat.end_s:g}s)")
        for character_id, spot in blocking.spots.items():
            lines.append(
                f"    {CAST[character_id].name:<16} at "
                f"({spot[0]:5.2f}, {spot[1]:5.2f}, {spot[2]:4.2f}) "
                f"facing {blocking.facings[character_id]:6.1f} deg")
        if len(blocking.pair) == 2:
            first, second = blocking.pair
            gap = gap_for_centre_distance(float(np.linalg.norm(
                (blocking.spots[first] - blocking.spots[second])[:2])))
            lines.append(
                f"    gap {gap:.2f} m between them -> {ring_for(gap)} ring")
        for cue_index, cue in enumerate(beat.actions):
            action = ACTIONS[cue.rig_action]
            start = director.cue_start(beat, cue_index)
            lines.append(
                f"    {start:5.2f}s {cue.rig_action} "
                f"({action.duration_s:g}s + {action.hold_s:g}s hold) "
                f"{CAST[cue.character_id].name}")
        sample = director.state_at(beat.start_s + beat.duration_s * 0.5)
        lines.append(f"    camera {sample.camera.shot_id} at "
                     f"{sample.camera.focal_mm:g} mm, "
                     f"{sample.camera.fov_deg:.1f} deg vertical")
        lines.append("")
    return "\n".join(lines)


def validate_drama_director() -> None:
    """Prove the timeline, the blocking and the shots for a whole episode."""
    from .drama_camera import EYE_LINE_FROM_TOP, eyeline_fraction
    from .drama_script import check_episode

    director = Director()
    assert not check_episode(director.episode)

    # Every instant of the episode has to resolve, including the last.
    for time_s in [index * 0.25 for index in range(0, 241)]:
        state = director.state_at(time_s)
        assert state.characters, time_s
        assert 0.0 <= state.beat_progress <= 1.0001, time_s
        assert state.camera.fov_deg > 0.0
        for character in state.characters.values():
            assert character.joints["head_top"][2] > 0.5, (time_s,
                                                           character.character_id)
            # Nobody may leave the dome they are standing in.
            reach = float(np.linalg.norm(character.spot[:2]))
            assert reach < state.dome_radius_m, (time_s, reach)

    # The hook: the slap fires, and the gasp answers it rather than
    # landing on top of it.
    hook = director.episode.beats[0]
    slap_start = director.cue_start(hook, 0)
    gasp_start = director.cue_start(hook, 1)
    assert gasp_start > slap_start
    assert gasp_start - slap_start >= ACTIONS["RIG_SLAP_EXECUTE"].duration_s

    during = director.state_at(slap_start + 0.20)
    assert during.characters["CHAR_AURELIA"].rig.action_id == \
        "RIG_SLAP_EXECUTE"
    assert during.characters["CHAR_AURELIA"].rig.amount > 0.5
    before_gasp = director.state_at(gasp_start - 0.05)
    assert before_gasp.characters["CHAR_LEO"].rig.action_id is None
    after_gasp = director.state_at(gasp_start + 0.10)
    assert after_gasp.characters["CHAR_LEO"].rig.action_id == \
        "RIG_GASP_REACTION"

    # The hook is a slap, so the pair must be inside the ring where a
    # slap can reach rather than at conversational spacing.
    hook_state = director.state_at(slap_start + 0.20)
    assert hook_state.characters["CHAR_AURELIA"].ring == "confrontation",         hook_state.characters["CHAR_AURELIA"].ring

    # The escalation puts Leo inside the confrontation ring, because the
    # script asked for half a metre.
    escalation = director.state_at(director.episode.beats[1].start_s + 2.0)
    assert escalation.characters["CHAR_LEO"].ring in ("confrontation",
                                                      "contact")

    # The camera keeps the eye-line on the third line for the framed
    # shots, on the real 1080x1920 frame.
    for time_s, subject in ((1.0, "CHAR_AURELIA"), (12.0, "CHAR_LEO")):
        state = director.state_at(time_s)
        landed = eyeline_fraction(state.camera,
                                  state.characters[subject].eye)
        assert abs(landed - EYE_LINE_FROM_TOP) < 0.05, (time_s, landed)

    # The reveal stands Silas under the apex, where the script put him.
    reveal = director.state_at(30.0)
    silas = reveal.characters["CHAR_SILAS"]
    assert float(np.linalg.norm(silas.spot[:2])) < 1.0, silas.spot

    # The cliffhanger puts Jax up in the struts, off the floor.
    cliff = director.state_at(50.0)
    assert cliff.characters["CHAR_JAX"].spot[2] > 2.5

    # A grab attaches; nothing else does.
    for state in (during, escalation, reveal):
        for character in state.characters.values():
            if character.rig.action_id == "RIG_GRAB_LAPEL":
                assert character.attached_to is not None
            else:
                assert character.attached_to is None or \
                    ACTIONS[character.rig.action_id].attach is not None

    # A full frame stream runs end to end at the published rate.
    frames = list(director.frames(30))
    assert len(frames) == int(round(director.episode.duration_s * 30))
    assert frames[0].beat.dramatic_beat == "COLD_HOOK"
    assert frames[-1].beat.dramatic_beat == "CLIFFHANGER"

    report = director_report()
    assert "DIRECTOR PLAN" in report and "confrontation ring" in report
