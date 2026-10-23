"""Nearly Level: original PG-13 family comedy, directed by sketch-gpt.

Captioned animatic by default. Scripted jaw timing is not a recorded voice track.
The episode's own closing title is its outro; no promotional segments are spliced
into the family dialogue. Both frame shapes use explicitly recomposed cameras.
"""
from __future__ import annotations

import json

from world3d import cinema as cm
from . import cabin_world as cw
from .lessons import Chapter, Lesson

PROJECT=cm.load_episode()


def clip_for(chapter):
    return next((i,c) for i,c in enumerate(PROJECT.clips) if c.id==chapter.stage)


def paint(app,opaque,transparent,p):
    chapter=app.chapters[app.chapter_index]
    i,clip=clip_for(chapter)
    time_s=float(PROJECT.starts()[i]+clip.duration*min(p,1-1e-8))
    cw.paint(app,hide=("builder",),subject=False)
    app.static_layer("sketch-gpt:episode-props",cm.set_props)
    opaque.vertices.extend(cm.cast_geometry(PROJECT,time_s).vertices)


def camera(app,chapter,p,width,height):
    _,clip=clip_for(chapter)
    return cm.shot_camera(PROJECT,clip,p,width/height)


def report():
    return json.dumps({"title":PROJECT.title,"episode":PROJECT.episode,
        "shots":[cm.analysis(PROJECT,i) for i in range(len(PROJECT.clips))]},indent=2)


def validate():
    cm.selftest(); PROJECT.validate()
    assert {a.age for a in PROJECT.cast if a.role.startswith(("Older sister","Brother"))}=={18,19}


def overlay(app,width,height):
    pg=app.pygame
    surface=pg.Surface((width,height),pg.SRCALPHA)
    chapter=app.chapters[app.chapter_index]
    if chapter.stage not in {c.id for c in PROJECT.clips}:
        return app.draw_ui_hype(width,height)
    _,clip=clip_for(chapter)
    portrait=width<height; margin=max(16,int(width*.045))
    unit=width/960 if not portrait else width/650
    small=app.font(max(14,int(19*unit)),True)
    font=app.font(max(20,int(29*unit)),True)
    surface.fill((0,0,0,0)); app.ui_buttons.clear()
    pg.draw.rect(surface,(13,35,32,210),(0,0,width,int(60*unit)))
    kicker=f"NEARLY LEVEL / {clip.title}"
    surface.blit(small.render(kicker,True,(240,224,184)),(margin,int(16*unit)))
    if clip.caption:
        meme=app.font(max(16,int(23*unit)),True)
        lines=app.wrap_text(clip.caption,meme,width-margin*2)
        for j,line in enumerate(lines):
            shadow=meme.render(line,True,(20,30,25)); text=meme.render(line,True,(255,226,154))
            x=(width-text.get_width())//2; y=int(height*.12)+j*meme.get_linesize()
            surface.blit(shadow,(x+2,y+2)); surface.blit(text,(x,y))
    speaker=next((a.name for a in PROJECT.cast if a.id==clip.speaker),"")
    dialogue=(speaker+": " if speaker else "")+clip.dialogue
    lines=app.wrap_text(dialogue,font,width-margin*2)
    block=len(lines)*font.get_linesize()+margin*2
    top=height-block-int(height*.045)
    pg.draw.rect(surface,(9,24,23,225),(0,top-margin//2,width,height-top))
    for j,line in enumerate(lines):
        surface.blit(font.render(line,True,(246,240,219)),(margin,top+j*font.get_linesize()))
    return surface


CHAPTERS=tuple(Chapter(c.id,f"{i+1:02d}",
    (next((a.name for a in PROJECT.cast if a.id==c.speaker),PROJECT.title)+" / "+c.caption),
    c.dialogue or c.title,(c.dialogue or c.title,),(),c.duration,(0,0,0),c.id)
    for i,c in enumerate(PROJECT.clips))

SKETCH_GPT_EPISODE=Lesson(key=cm.LESSON_KEY,brand="sketch-gpt",title=f"{PROJECT.title}: {PROJECT.episode}",
    chapters=CHAPTERS,scenes={c.id:paint for c in PROJECT.clips},selftest=validate,report=report,
    snapshot_prefix="nearly-level",style="hype",camera_fn=camera,
    ground="off",backdrop=cw.backdrop,light=cw.LIGHT,frame_fit="off",ui_fn=overlay)
