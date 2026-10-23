"""sketch-gpt cinematic timeline, camera flight and original family ensemble.

Metres, seconds, degrees. Cabin World landmarks and existing figure/face/shot
machinery are authoritative; this module adds direction, not another dome.
"""
from __future__ import annotations

import copy
import csv
import json
import math
import os
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from functools import lru_cache

import numpy as np

from two_v_demo import shots
from two_v_demo import cabin_world as cw
from two_v_demo.drama_camera import fov_for_focal
from two_v_demo.drama_face import draw_face, face_for
from two_v_demo.figure import POSES, Pose, draw_figure, joint_positions
from two_v_demo.render_kit import TriangleBatch, look_at, perspective, project_point

ROOT = Path(__file__).resolve().parents[1]
SAVE = ROOT / "world3d/saved/sketch-gpt-episode.json"
SCHEMA = "sketch-gpt.episode/1"
LESSON_KEY = "sketch_gpt_pilot"
MOVES = ("hold", "push in", "pull out", "slide left", "slide right", "pan", "tilt",
         "orbit", "crane", "dolly zoom", "spline")
ACTIONS = ("listen", "talk", "shrug", "point", "facepalm", "carry", "walk", "react")
CONSTANTS = {
    "walk_eye_height_m": 1.65, "walk_speed_m_s": 1.5,
    "drone_speed_m_s": 4.0, "drone_damping_per_s": 5.0,
    "sensor_height_mm": 24.0, "camera_near_m": 0.05,
    "workbench_size_m": [1.8, .65, .85], "shelf_length_m": 1.2,
    "character_pose_samples_hz": 8,
    "note": "Camera ergonomics, prop dimensions and fictional cast are declared creative choices, not dome measurements.",
}


@dataclass
class Actor:
    id: str
    name: str
    age: int
    role: str
    stature: float
    position: list[float]
    shirt: list[float]
    hair: list[float]


@dataclass
class Clip:
    id: str
    title: str
    duration: float
    move: str = "hold"
    focus: str = "family"
    lens: float = 35.0
    end_lens: float = 35.0
    distance: float = 4.0
    end_distance: float = 3.0
    yaw: float = -90.0
    sweep: float = 24.0
    height: float = .2
    easing: str = "smooth"
    speaker: str = ""
    dialogue: str = ""
    action: str = "talk"
    reaction: str = "listen"
    caption: str = ""
    keyframes: list[dict] = field(default_factory=list)
    blocking: dict = field(default_factory=dict)
    marker: str = ""


@dataclass
class Episode:
    title: str
    episode: str
    cast: list[Actor]
    clips: list[Clip]
    fps: int = 24
    markers: list[dict] = field(default_factory=list)

    @property
    def duration(self):
        return sum(c.duration for c in self.clips)

    def locate(self, time_s):
        t = min(max(0., float(time_s)), max(0., self.duration - 1e-8))
        start = 0.
        for i, clip in enumerate(self.clips):
            if t < start + clip.duration:
                return i, clip, (t-start)/clip.duration, start
            start += clip.duration
        raise ValueError("Empty timeline")

    def starts(self):
        return np.r_[0., np.cumsum([c.duration for c in self.clips])]

    def validate(self):
        if not self.clips or len(self.clips)>500 or not 1<=len(self.cast)<=30:
            raise ValueError("Use 1-500 shots and at most 30 actors.")
        if not 1<=self.fps<=120:
            raise ValueError("Frame rate must be between 1 and 120.")
        ids = {a.id for a in self.cast}
        if len(ids)!=len(self.cast) or len({c.id for c in self.clips})!=len(self.clips):
            raise ValueError("Actor and shot IDs must be unique.")
        for actor in self.cast:
            values=np.array([actor.stature,*actor.position,*actor.shirt,*actor.hair],float)
            if len(actor.position)!=3 or len(actor.shirt)!=3 or len(actor.hair)!=3 or not np.isfinite(values).all():
                raise ValueError("Invalid actor geometry or costume.")
            if not 1.2<=actor.stature<=2.3 or actor.age<18:
                raise ValueError("The pilot ensemble is adult; use realistic declared stature.")
        for c in self.clips:
            values = [c.duration,c.lens,c.end_lens,c.distance,c.end_distance,c.yaw,c.sweep,c.height]
            if not np.isfinite(values).all() or not .6<=c.duration<=300:
                raise ValueError("Shot duration must be finite and between 0.6 and 300 seconds.")
            if c.move not in MOVES or c.easing not in ("smooth","linear","ease out"):
                raise ValueError("Unknown move or easing curve.")
            if c.focus not in ids | {"family","dome","bench","log"} or c.speaker not in ids | {""}:
                raise ValueError("Unknown focus or speaker.")
            if c.action not in ACTIONS or c.reaction not in ACTIONS:
                raise ValueError("Unknown actor action.")
            if not 12<=c.lens<=200 or not 12<=c.end_lens<=200 or min(c.distance,c.end_distance)<.3:
                raise ValueError("Lens must be 12-200 mm and camera distance at least 0.3 m.")
            for key in c.keyframes:
                if set(key)!={"eye","target","lens"} or len(key["eye"])!=3 or len(key["target"])!=3:
                    raise ValueError("Camera keys need eye, target and lens.")
                if not np.isfinite([*key["eye"],*key["target"],key["lens"]]).all() or not 12<=key["lens"]<=200:
                    raise ValueError("Invalid camera key.")
                if np.linalg.norm(np.array(key["eye"])-key["target"])<.05:
                    raise ValueError("A camera cannot look at its own position.")
            if c.move=="spline" and len(c.keyframes)<2:
                raise ValueError("A spline needs at least two captured camera keys.")
            for who, path in c.blocking.items():
                if who not in ids or set(path)!={"from","to"} or any(len(path[k])!=3 for k in path):
                    raise ValueError("Blocking needs a known actor and from/to 3D positions.")
                if not np.isfinite([path["from"],path["to"]]).all():
                    raise ValueError("Blocking coordinates must be finite.")

    def save(self,path=SAVE):
        self.validate()
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
        data={"schema":SCHEMA,"units":"metres, seconds, degrees", "constants":CONSTANTS, **asdict(self)}
        tmp=path.with_suffix(path.suffix+".tmp")
        tmp.write_text(json.dumps(data,indent=2),encoding="utf-8"); os.replace(tmp,path)
        return path


def default_episode():
    cast=[Actor("cal","Cal",45,"Dad: confident DIY improviser",1.81,[-1.15,-.25,0],[.72,.39,.16],[.24,.15,.10]),
          Actor("mara","Mara",44,"Mom: dry wit and practical judgement",1.70,[1.15,.45,0],[.22,.47,.44],[.16,.10,.08]),
          Actor("june","June",19,"Older sister: deadpan editor of family reality",1.72,[1.05,-.65,0],[.57,.32,.57],[.21,.12,.08]),
          Actor("theo","Theo",18,"Brother: overconfident optimization enthusiast",1.80,[-.3,.65,0],[.25,.42,.66],[.21,.14,.09]),
          Actor("milo","Milo",18,"Brother: sincere chaos and accidental wisdom",1.76,[-1.65,.7,0],[.45,.54,.27],[.43,.29,.16])]
    rows=[
        ("Cold open",7,"crane","family","cal","Today we build one shelf. No apps. No drama.","point","The family has entered the chat."),
        ("Terms and conditions",6,"slide left","june","june","Bold of you to ban the two things keeping this family employed.","shrug","UNPAID FAMILY IT DEPARTMENT"),
        ("Smart shelf",7,"push in","theo","theo","I made it smart. It sends a notification when something falls off.","talk","DISRUPTING GRAVITY"),
        ("Beta testing",5,"pan","milo","milo","So... a shelf with anxiety. Finally, furniture that gets me.","react","SELF-AWARE SHELVING"),
        ("Dad's calibration",7,"dolly zoom","cal","cal","The bubble is centered. The wall must be wrong.","point","CONFIDENCE: LOAD BEARING"),
        ("Mom's inspection",6,"slide right","mara","mara","Honey, that's the camera app. You're leveling the selfie.","facepalm","CHECK THE TOOL, CAL"),
        ("Influencer mode",6,"orbit","june","june","Keep rolling. This is the first renovation with a reaction channel.","talk","SHELF ESTEEM: EPISODE ONE"),
        ("The fix",8,"push in","milo","milo","What if we just put the books on the table? It's been a shelf with legs this whole time.","shrug","ACCIDENTALLY INVENTS A TABLE"),
        ("The receipt",6,"pull out","family","mara","Great. Now somebody improve this home by doing the damn dishes.","point","HOME IMPROVEMENT: DISHES DLC"),
        ("Tag",5,"hold","cal","cal","Next week: a dishwasher. I'm thinking Bluetooth.","talk","TO BE CONTINUED. UNFORTUNATELY."),
    ]
    clips=[]
    for i,(title,duration,move,focus,speaker,line,action,caption) in enumerate(rows):
        wide=focus=="family"
        clips.append(Clip(f"shot-{i+1:02d}",title,duration,move,focus,
            lens=28 if wide else 42,end_lens=28 if wide else 42,
            distance=7.4 if wide else 2.0,end_distance=5.5 if wide else 1.5,
            yaw=-90,sweep=24,height=.35,speaker=speaker,dialogue=line,
            action=action,reaction="listen",caption=caption,
            marker="cold open" if i==0 else ("punchline" if i in (3,5,7,8,9) else "setup")))
    clips[0].height=2.4
    clips[3].sweep=15
    clips[5].yaw=-50
    clips[5].distance=1.7
    clips[5].end_distance=1.4
    clips.append(Clip("closing-title","Nearly Level",3,"crane","dome",lens=28,end_lens=28,
        distance=9,end_distance=7,height=2.5,dialogue="Nearly Level. Same family. Fewer right angles.",
        caption="NEXT TIME: THE BLUETOOTH DISHWASHER",marker="series outro"))
    return Episode("Nearly Level", "S01E01 / Shelf Esteem",cast,clips)


def load_episode(path=None):
    path=Path(path or os.environ.get("SKETCH_GPT_EPISODE_PROJECT",SAVE))
    if not path.exists():
        return default_episode()
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema")!=SCHEMA:
        raise ValueError("Unsupported sketch-gpt episode schema.")
    ep=Episode(data["title"],data["episode"],[Actor(**a) for a in data["cast"]],
               [Clip(**c) for c in data["clips"]],data.get("fps",24),data.get("markers",[]))
    ep.validate(); return ep


def eased(p,curve):
    p=float(np.clip(p,0,1))
    return p if curve=="linear" else (1-(1-p)**3 if curve=="ease out" else shots.ease(p))


def actor_root(actor,clip,p):
    path=clip.blocking.get(actor.id)
    at=np.array(actor.position,float)
    if path:
        at=np.array(path["from"])+(np.array(path["to"])-path["from"])*shots.ease(p)
    return cw.landmarks().deck_centre+at


def subject(ep,clip,p):
    m=cw.landmarks()
    if clip.focus=="dome": return m.dome_centre+[0,0,m.dome_r*.45]
    if clip.focus=="bench": return m.deck_centre+[0,.15,.85]
    if clip.focus=="log": return m.log_end
    if clip.focus=="family": return m.deck_centre+[0,0,1.1]
    actor=next(a for a in ep.cast if a.id==clip.focus)
    return actor_root(actor,clip,p)+[0,0,actor.stature*.86]


def shot_camera(ep,clip,p,aspect=16/9):
    target=np.asarray(subject(ep,clip,p),float)
    # Existing shot factories have smooth timing built in. Warp their progress
    # only for the alternate user-selected curves, avoiding double easing.
    t=eased(p,clip.easing)
    a=math.radians(clip.yaw)
    direction=np.array([math.cos(a),math.sin(a),0.])
    eye0=target+direction*clip.distance+[0,0,clip.height]
    eye1=target+direction*clip.end_distance+[0,0,clip.height]
    focal=clip.lens+(clip.end_lens-clip.lens)*t
    fov=fov_for_focal(focal)
    if clip.move in ("push in","pull out"):
        start,end=(eye0,eye1) if clip.move=="push in" else (eye1,eye0)
        eye=start+(end-start)*t
    elif clip.move in ("slide left","slide right"):
        side=np.array([-direction[1],direction[0],0.])
        eye=eye0+side*(t-.5)*clip.sweep/12*(1 if clip.move=="slide right" else -1)
    elif clip.move=="orbit":
        # Reuse the shared orbit implementation and invert its ease for custom timing.
        angle=math.radians(clip.yaw+clip.sweep*t)
        eye=target+np.array([math.cos(angle)*clip.distance,math.sin(angle)*clip.distance,clip.height])
    elif clip.move=="crane":
        eye=eye1+(eye0-eye1)*t+[0,0,clip.height*t]
    elif clip.move=="dolly zoom":
        # Preserve projected subject size using the actual 3-D eye-target distance.
        eye=eye0+(eye1-eye0)*t
        reach0=np.linalg.norm(eye0-target); reach=np.linalg.norm(eye-target)
        fov=math.degrees(2*math.atan(math.tan(math.radians(fov_for_focal(clip.lens))/2)*reach0/reach))
    elif clip.move=="spline":
        key=clip.keyframes
        eye=shots._catmull([np.array(k["eye"],float) for k in key],t)
        target=shots._catmull([np.array(k["target"],float) for k in key],t)
        focal=float(np.interp(t,np.linspace(0,1,len(key)),[k["lens"] for k in key])); fov=fov_for_focal(focal)
    else:
        eye=eye0
        if clip.move=="pan":
            v=target-eye; angle=math.radians(clip.sweep*(t-.5)); x,y=v[:2]
            target=eye+np.array([x*math.cos(angle)-y*math.sin(angle),x*math.sin(angle)+y*math.cos(angle),v[2]])
        elif clip.move=="tilt":
            target=target+[0,0,math.tan(math.radians(clip.sweep*(t-.5)))*clip.distance]
    # A phone cut widens the lens to preserve horizontal coverage instead of
    # simply cropping every family member off the sides.
    if aspect<1:
        fov=math.degrees(2*math.atan(math.tan(math.radians(fov)/2)*(16/9)/aspect))
    return np.asarray(eye,float),np.asarray(target,float),float(np.clip(fov,8,135))


def pose_for(action,t,progress):
    rest=POSES["stand"]
    amount=.5+.5*math.sin(math.pi*progress)
    if action=="walk": return POSES["stride"].blend(POSES["stride_pass"],.5+.5*math.sin(t*7))
    values={
        "talk":dict(r_shoulder=36+8*math.sin(t*3),r_elbow=55),
        "shrug":dict(l_shoulder=35,r_shoulder=35,l_shoulder_out=35,r_shoulder_out=35,l_elbow=100,r_elbow=100),
        "point":dict(r_shoulder=85,r_elbow=12,trunk_twist=-8),
        "facepalm":dict(r_shoulder=85,r_elbow=125,neck=15),
        "react":dict(l_shoulder=30,r_shoulder=40,l_elbow=100,r_elbow=90,trunk_lean=-6),
    }
    if action=="carry": return POSES["carry"]
    return rest.blend(replace(rest,**values.get(action,{})),amount)


class CastBatch(TriangleBatch):
    """The existing rig at animatic mesh detail, preserving its real joints."""
    def sphere(self,center,radius,color,rings=5,segments=8):
        return super().sphere(center,radius,color,min(rings,3),min(segments,6))


@lru_cache(maxsize=320)
def _actor_mesh(actor_spec,action,phase,progress,text,duration):
    ident,stature,shirt,hair=actor_spec
    joints=joint_positions(pose_for(action,phase,progress),stature)
    batch=CastBatch()
    draw_figure(batch,joints,hi_vis=(*shirt,1),trousers=(.17,.21,.25,1),helmet=(*hair,1),scale=stature/1.78)
    expression="RIG_GASP_REACTION" if action=="react" else ("RIG_DISDAINFUL_TURN" if action=="facepalm" else None)
    draw_face(batch,joints,face_for(ident,expression,.7,phase,text,progress*duration,duration))
    if ident in ("june","mara"):
        batch.sphere(joints["neck"]+[-.06,0,.04],.115,(*hair,1),3,6)
    if action=="carry":
        hand=(joints["l_grip"]+joints["r_grip"])/2
        batch.box(hand,(CONSTANTS["shelf_length_m"],.18,.035),(.63,.39,.18,1))
    return np.asarray(batch.vertices,dtype='f4').reshape(-1,10)


def cast_geometry(ep,time_s):
    _,clip,p,_=ep.locate(time_s); parts=[]
    for actor in ep.cast:
        root=actor_root(actor,clip,p); facing=np.array([0.,-4.,root[2]])-root
        yaw=math.atan2(facing[1],facing[0]); co,si=math.cos(yaw),math.sin(yaw)
        rotation=np.array([[co,-si,0],[si,co,0],[0,0,1]])
        action=clip.action if actor.id==clip.speaker else clip.reaction
        text=clip.dialogue if actor.id==clip.speaker else ""
        # Listener meshes are immutable; speaking animation is sampled at 8 Hz.
        # Camera motion still evaluates continuously at the output frame rate.
        phase=round((time_s%8)*8)/8 if action!="listen" else 0
        progress=round(p*16)/16 if action!="listen" else 0
        spec=(actor.id,actor.stature,tuple(actor.shirt),tuple(actor.hair))
        data=_actor_mesh(spec,action,phase,progress,text,clip.duration if text else 0).copy()
        data[:,:3]=data[:,:3]@rotation.T+root; data[:,3:6]=data[:,3:6]@rotation.T
        parts.append(data)
    batch=TriangleBatch(); batch.vertices=np.concatenate(parts).ravel().tolist()
    return batch


@lru_cache(maxsize=1)
def set_props():
    m=cw.landmarks(); batch=TriangleBatch(); d=np.array(CONSTANTS["workbench_size_m"])
    center=m.deck_centre+[0,.2,d[2]-.035]
    batch.box(center,(d[0],d[1],.07),(.62,.40,.23,1))
    for x in (-.78,.78):
        for y in (-.23,.23):
            batch.box(m.deck_centre+[x,.2+y,.4],(.065,.065,.8),(.22,.29,.28,1))
    batch.box(center+[0,0,.07],(CONSTANTS["shelf_length_m"],.18,.035),(.78,.57,.30,1))
    batch.box(center+[.36,-.12,.11],(.2,.07,.035),(.18,.22,.23,1))
    return batch


@dataclass
class Flight:
    eye: np.ndarray
    yaw: float = 90.
    pitch: float = 0.
    lens: float = 28.
    velocity: np.ndarray = field(default_factory=lambda:np.zeros(3))
    mode: str = "walk"
    speed: float = 1.5
    damping: float = 5.

    @classmethod
    def home(cls,mode="walk"):
        m=cw.landmarks()
        eye=m.deck_centre+[0,-m.deck_r*.72,CONSTANTS["walk_eye_height_m"]]
        return cls(eye,mode=mode,speed=CONSTANTS["drone_speed_m_s"] if mode=="drone" else CONSTANTS["walk_speed_m_s"])

    def look(self,dx,dy):
        self.yaw+=dx*.18; self.pitch=float(np.clip(self.pitch-dy*.18,-85,85))

    def state(self):
        a,b=math.radians(self.yaw),math.radians(self.pitch)
        direction=np.array([math.cos(a)*math.cos(b),math.sin(a)*math.cos(b),math.sin(b)])
        return self.eye.copy(),self.eye+direction,fov_for_focal(self.lens)

    def step(self,keys,dt,boost=False):
        dt=float(np.clip(dt,0,.2))
        a=math.radians(self.yaw); forward=np.array([math.cos(a),math.sin(a),0.])
        if self.mode=="drone":
            _,target,_=self.state(); forward=target-self.eye
        side=np.array([math.sin(a),-math.cos(a),0.])
        desired=forward*(int("w" in keys)-int("s" in keys))+side*(int("d" in keys)-int("a" in keys))
        if self.mode=="drone": desired[2]+=int("e" in keys)-int("q" in keys)
        length=np.linalg.norm(desired)
        if length>1: desired/=length
        desired*=self.speed*(3 if boost else 1)
        self.velocity+=(desired-self.velocity)*(1-math.exp(-self.damping*dt))
        self.eye+=self.velocity*dt
        m=cw.landmarks()
        if self.mode=="walk":
            # Floor/deck support is modeled; this is a camera scout, not an avatar
            # collision simulation. Structural collision remains deliberately off.
            z=m.deck_centre[2] if np.linalg.norm(self.eye[:2]-m.deck_centre[:2])<m.deck_r else 0.
            self.eye[2]=z+CONSTANTS["walk_eye_height_m"]; self.velocity[2]=0
        else: self.eye[2]=max(.2,self.eye[2])


@lru_cache(maxsize=1)
def structure_triangles():
    return np.asarray(cw.layer('dome').vertices,float).reshape(-1,3,10)[:,:,:3]


def analysis(ep,clip_index,width=960,height=540):
    clip=ep.clips[clip_index]
    starts=ep.starts(); times=np.linspace(0,clip.duration,31)
    cameras=[shot_camera(ep,clip,t/clip.duration,width/height) for t in times]
    eyes=np.array([c[0] for c in cameras]); targets=np.array([c[1] for c in cameras])
    speed=np.linalg.norm(np.diff(eyes,axis=0),axis=1)/np.diff(times)
    directions=targets-eyes; directions/=np.linalg.norm(directions,axis=1)[:,None]
    angular=np.degrees(np.arccos(np.clip(np.sum(directions[1:]*directions[:-1],axis=1),-1,1)))/np.diff(times)
    framing=[]; occlusion=[]
    from .pieces import ray_hit
    for p,(eye,target,fov) in zip(np.linspace(0,1,31),cameras):
        mvp=perspective(fov,width/height,.05,400)@look_at(eye,target)
        focus=project_point(mvp,subject(ep,clip,p),width,height)
        framing.append(focus is not None and 0<=focus[0]<=width and 0<=focus[1]<=height)
        subject_point=subject(ep,clip,p); reach=np.linalg.norm(subject_point-eye)
        hit=ray_hit(structure_triangles(),eye,(subject_point-eye)/reach)
        occlusion.append(hit is not None and hit<reach-.1)
    words=len(clip.dialogue.split())
    return {"shot":clip.id,"start_s":float(starts[clip_index]),"duration_s":clip.duration,
            "times":times.tolist(),"speed_m_s":speed.tolist(),"angular_deg_s":angular.tolist(),
            "peak_speed_m_s":float(max(speed)),"peak_angular_deg_s":float(max(angular)),
            "path_length_m":float(np.sum(np.linalg.norm(np.diff(eyes,axis=0),axis=1))),
            "dialogue_wpm":words/clip.duration*60,"focus_in_frame_fraction":sum(framing)/len(framing),
            "structure_occlusion_fraction":sum(occlusion)/len(occlusion),
            "warnings":(["Dialogue exceeds 190 words/minute"] if words/clip.duration*60>190 else [])+
                       (["Focus leaves the frame"] if not all(framing) else [])+
                       (["Fast pan: review for comfort"] if max(angular)>90 else [])+
                       (["Timber occludes the focus in sampled frames"] if sum(occlusion)/len(occlusion)>.2 else [])}


def motion_clip(data,ident="motion-take"):
    """Resample timestamped takes before spline playback; variable UI/render rates
    must not speed up the slowest captured part of a camera move."""
    if data.get("schema")!="sketch-gpt.motion/1": raise ValueError("Unsupported motion take schema.")
    samples=data.get("samples",[])
    if not 2<=len(samples)<=10000: raise ValueError("A motion take needs 2-10000 samples.")
    times=np.array([s["time_s"] for s in samples],float)
    if not np.isfinite(times).all() or np.any(np.diff(times)<=0): raise ValueError("Take timestamps must increase.")
    duration=float(times[-1]-times[0])
    if not .6<=duration<=300: raise ValueError("A take must last 0.6-300 seconds.")
    positions=np.array([[*s["eye"],*s["target"],s["lens"]] for s in samples],float)
    if positions.shape!=(len(samples),7) or not np.isfinite(positions).all(): raise ValueError("Invalid camera sample.")
    clock=np.linspace(times[0],times[-1],min(600,max(2,math.ceil(duration*12))))
    interpolated=np.column_stack([np.interp(clock,times,positions[:,j]) for j in range(7)])
    keys=[{"eye":row[:3].tolist(),"target":row[3:6].tolist(),"lens":float(row[6])} for row in interpolated]
    return Clip(ident,"Recorded camera take",duration,"spline",easing="linear",keyframes=keys)


class Preview:
    """Persistent Cabin World renderer; same set and articulated figures as the film."""
    def __init__(self,width=960,height=540):
        self.studio=cw.Studio(width,height,samples=4)
        self.width,self.height=width,height
        self.props=set_props()
        self._cast_key=None; self._cast=None

    def frame(self,ep,t,camera=None,guides=True,caption=True):
        from PIL import Image, ImageDraw, ImageFont
        _,clip,p,_=ep.locate(t)
        eye,target,fov=camera or shot_camera(ep,clip,p,self.width/self.height)
        key=(id(ep),round(t,4),repr(ep.clips[ep.locate(t)[0]].blocking))
        if key!=self._cast_key:
            self._cast=cast_geometry(ep,t); self._cast_key=key
        raw=self.studio.frame(eye,target,fov,extra=(self.props,self._cast),hide=("builder",))
        im=Image.fromarray(np.uint8(np.clip(raw,0,1)*255)); dr=ImageDraw.Draw(im)
        if guides:
            for frac in (1/3,2/3):
                dr.line((self.width*frac,0,self.width*frac,self.height),fill="#a3b4a0",width=1)
                dr.line((0,self.height*frac,self.width,self.height*frac),fill="#a3b4a0",width=1)
            dr.rectangle((self.width*.05,self.height*.05,self.width*.95,self.height*.95),outline="#d7bb78",width=1)
            # Centre 9:16 guide inside landscape; actual phone camera is re-framed.
            if self.width>self.height:
                side=(self.width-self.height*9/16)/2
                dr.rectangle((side,0,self.width-side,self.height),outline="#83b7b1",width=1)
        font_path="C:/Windows/Fonts/segoeuib.ttf"
        size=max(14,int(self.height*.035)); font=ImageFont.truetype(font_path,size)
        dr.rectangle((0,0,self.width,32),fill="#173c39")
        dr.text((12,5),f"{ep.title} / {clip.title} / sketch-gpt",font=font,fill="#f7ead0")
        if caption and clip.caption:
            meme_font=ImageFont.truetype(font_path,max(14,int(self.height*.035)))
            words=clip.caption.split(); lines=[]; line=''
            for word in words:
                trial=(line+' '+word).strip()
                if dr.textlength(trial,font=meme_font)>self.width*.85 and line:
                    lines.append(line); line=word
                else: line=trial
            if line: lines.append(line)
            for j,line in enumerate(lines):
                dr.text((self.width/2,self.height*.14+j*(size+4)),line,font=meme_font,
                    fill='#ffe29a',stroke_width=2,stroke_fill='#24382f',anchor='mm')
        if caption and clip.dialogue:
            speaker=next((a.name for a in ep.cast if a.id==clip.speaker),"")
            text=f"{speaker}: {clip.dialogue}"; words=text.split(); lines=[]; line=""
            for word in words:
                trial=(line+" "+word).strip()
                if dr.textlength(trial,font=font)>self.width*.9 and line: lines.append(line); line=word
                else: line=trial
            if line: lines.append(line)
            top=self.height-len(lines)*(size+7)-15
            dr.rectangle((0,top-7,self.width,self.height),fill="#17302f")
            for j,line in enumerate(lines): dr.text((self.width*.05,top+j*(size+7)),line,font=font,fill="#f6f0dc")
        return im

    def close(self): self.studio.release()


def export_edit(ep):
    """Reviewable production package. Films still go through `film make`."""
    import medialib
    ep.validate(); folder=medialib.new_folder("sketch-gpt-nearly-level-edit")
    ep.save(folder/"episode.json")
    preview=Preview(960,540)
    try:
        for i,c in enumerate(ep.clips):
            preview.frame(ep,float(ep.starts()[i]+c.duration*.5),guides=True).save(folder/f"shot-{i+1:02d}.jpg",quality=94)
    finally: preview.close()
    reports=[analysis(ep,i) for i in range(len(ep.clips))]
    (folder/"analysis.json").write_text(json.dumps(reports,indent=2),encoding="utf-8")
    with (folder/"shot-list.csv").open("x",newline="",encoding="utf-8") as f:
        writer=csv.writer(f); writer.writerow(["shot","in_s","out_s","move","focus","lens_mm","speaker","dialogue","action"])
        for start,c in zip(ep.starts(),ep.clips): writer.writerow([c.id,start,start+c.duration,c.move,c.focus,c.lens,c.speaker,c.dialogue,c.action])
    def tc(seconds):
        frame=round(seconds*ep.fps); sec,fr=divmod(frame,ep.fps); mins,sec=divmod(sec,60); hrs,mins=divmod(mins,60)
        return f"{hrs:02d}:{mins:02d}:{sec:02d}:{fr:02d}"
    edl=[f"TITLE: {ep.title} - {ep.episode}","FCM: NON-DROP FRAME"]
    script=[f"# {ep.title}\n\n{ep.episode}\n\nOriginal family comedy; PG-13 target.\n"]
    for i,(start,c) in enumerate(zip(ep.starts(),ep.clips),1):
        edl+=[f"{i:03d}  AX       V     C        {tc(0)} {tc(c.duration)} {tc(start)} {tc(start+c.duration)}",f"* FROM CLIP NAME: {c.id}"]
        script+=[f"## {i:02d}. {c.title} / {c.move}\n\n{c.speaker.upper()}: {c.dialogue}\n\nAction: {c.action}. Meme: {c.caption}\n"]
    (folder/"timeline.edl").write_text("\n".join(edl)+"\n",encoding="utf-8")
    (folder/"script.md").write_text("\n".join(script),encoding="utf-8")
    (folder/"README.md").write_text("# sketch-gpt production edit\n\nJSON is the complete camera, cast and dialogue source. EDL is a non-drop-frame cut list, not rendered media.\n\n"
        "Floor support is modeled; camera/structure collision is off. Spline speed is time-parametric, not constant-distance. Faces use text-timed jaw motion, not audio phoneme sync.\n\n"
        "Render via the registered sketch_gpt_pilot film. This package is a storyboard and edit export, not a finished episode.\n",encoding="utf-8")
    medialib.write_index(); return folder


def selftest():
    import tempfile
    ep=default_episode(); ep.validate()
    for i,c in enumerate(ep.clips):
        for p in (0,.5,1):
            for aspect in (16/9,9/16):
                eye,target,fov=shot_camera(ep,c,p,aspect)
                assert np.isfinite([eye,target]).all() and 0<fov<150 and np.linalg.norm(eye-target)>.05
        assert analysis(ep,i)["focus_in_frame_fraction"]>.8
    c=ep.clips[0]
    for move in MOVES:
        c=replace(c,move=move,keyframes=[{"eye":[0,-6,2],"target":[0,0,1],"lens":28},{"eye":[1,-4,3],"target":[0,0,1],"lens":35}])
        for p in (0,.5,1): assert np.isfinite(shot_camera(ep,c,p)[0]).all()
    c=replace(ep.clips[4],move="dolly zoom")
    sizes=[]
    for p in (0,.5,1):
        eye,target,fov=shot_camera(ep,c,p); sizes.append(np.linalg.norm(target-eye)*math.tan(math.radians(fov)/2))
    assert np.ptp(sizes)<1e-8
    assert ep.locate(ep.clips[0].duration)[0]==1
    flight=Flight.home("drone"); before=flight.eye.copy()
    for _ in range(10): flight.step({"w","e"},.1)
    assert np.linalg.norm(flight.eye-before)>.5 and flight.eye[2]>before[2]
    for _ in range(30): flight.step(set(),.1)
    assert np.linalg.norm(flight.velocity)<1e-5
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/"edit.json"; ep.save(path)
        assert asdict(load_episode(path))==asdict(ep)
        bad=copy.deepcopy(ep); bad.clips[0].duration=float('nan')
        try: bad.validate()
        except ValueError: pass
        else: raise AssertionError("NaN timeline accepted")
    take={"schema":"sketch-gpt.motion/1","samples":[
        {"time_s":t,"eye":[t,-4,2],"target":[0,0,1],"lens":28} for t in (0,.1,.6,1.8)]}
    motion=motion_clip(take)
    assert abs(motion.duration-1.8)<1e-9
    assert np.allclose(motion.keyframes[-1]['eye'],[1.8,-4,2])
    assert np.allclose(motion.keyframes[len(motion.keyframes)//2]['eye'][0],np.linspace(0,1.8,len(motion.keyframes))[len(motion.keyframes)//2])
    print("sketch-gpt cinema selftest: ok")


if __name__=="__main__": selftest()
