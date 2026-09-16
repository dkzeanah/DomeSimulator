"""The author's annotated Dome Park transcript, revised as a new cut.

The original lesson and its existing exports remain reproducible. This film
uses the same geometry, adds the requested moving concepts, and keeps the
author's targets separate from measured geometry and budget assumptions.
"""
from __future__ import annotations

from dataclasses import replace
import numpy as np
import park_model as pm
from . import lesson_dome_park as old, byod_facts as facts
from .byod_scenes import SCENES as NEW_SCENES, iris_radius
from .lessons import Chapter, Lesson
from .park_facts import steps_stay, steps_crossover, steps_hardware, steps_ask
from .render_kit import TriangleBatch
from .segments import OUTRO


def chapter(slug, title, promise, text, stage="dp_site", camera=(88., 20., 54.),
            equations=(), overlay=None, duration=12.):
    return Chapter(slug, "00", title, promise, tuple(text), tuple(equations),
                   duration, camera, stage, overlay)


def worksheet(slug, title, promise, text, lines, stage="byod_starter", camera=(50., 35., 22.)):
    return chapter(slug, title, promise, text, stage, camera, lines, "math", 24.)


def operating_steps():
    host, rental = pm.host_comparison(old.home_pad())
    return (
        "OPERATING SCENARIO / same declared base costs",
        f"Pad management, tax, insurance: ${host.yearly_costs:,.0f}/year",
        f"Short-let operating total: ${rental.yearly_costs:,.0f}/year",
        f"Cleaning: ${pm.declared('airbnb_turnover_usd'):,.0f} each turnover",
        f"Damage reserve: {pm.declared('airbnb_damage_reserve_fraction') * 100:.0f}% of revenue",
        f"Platform fee: {pm.declared('airbnb_platform_fee_fraction') * 100:.0f}% of revenue",
        f"Renovation allowance: ${pm.declared('rental_renovation_usd_per_year'):,.0f}/year",
        "Existing furnished building assumed; acquisition is excluded.",
        "Pad/deck and service maintenance still need provision.",
        "A smaller maintenance scope; not zero work or zero risk.",
    )


CHAPTERS = (
    chapter("title", "A home you keep", "BRING YOUR OWN DOME", (
        "Bring your own dome.",
        "Build a home. Improve it. Take it with you.",
    ), "byod_title", overlay="title", duration=8),
    chapter("open", "An RV park, for houses", "Serviced pads. You bring the home.", (
        "Think: fancier trailer park. Or maybe better, a stationary RV park where the thing you park is a house you built and can take apart again.",
        "A landowner builds a circular service pad. A dome owner arrives with their home, sets it down on the pad, and plugs in.",
        "These domes come from the Dome Creator and the wedge simulator. The same tools that design them draw them here.",
    )),
    chapter("why_host", "Why would someone host a dome?", "Income from the pad. Fewer household repairs.", (
        "Why would people want to host these things? Cash money. Income from land, without also buying and maintaining the home somebody else lives in.",
        "We know the pains of landlords. We know the pains of tenants. I want to bridge the two so the arrangement works for both. They love me, they love each other. That is the dream, anyway.",
        "The host still looks after the pad and the services. But replacing somebody's kitchen, sofa, or bedroom carpet is no longer the host's business.",
    )),
    chapter("why_owner", "Why buy the dome?", "Start small. Upgrade the home you own.", (
        "And why put your own money into a dome? Because a small personal home can start simple, then become more comfortable, larger, and better equipped as your life changes.",
        "My target for the basic trailer model of this system is a five thousand dollar dome, relying on the pad for the essentials. That is a design target, not a finished-home quote.",
        "Put the durable money into hardware planned for the current dome and two sizes beyond it. Then collect the longer members for the next build over time. We will come back to exactly what that means.",
    ), "byod_growth", (82., 23., 25.)),
    chapter("legend", "Two people. Clear responsibilities.", "Amber: the pad host. Cyan: the dome owner.", (
        "Amber is the pad host: the deck, the service connections, the meter. Cyan is the dome owner: the house and everything they do to it.",
        "The important line stays in the same place. The host provides the site. The resident owns the home.",
        "You still pay for the ground and the services, but the house you improve is yours. Both sides keep control of their own part, with fewer things held in common and a clearer goodbye when it is time to move.",
    ), "dp_legend"),
    chapter("center", "The reserved spot", "Utilities in the center. Choices around them.", (
        "The middle of the pad is the spot every builder knows to reserve for utilities. It is not the only way to do it. It is the way I want this system to work.",
        "Power, water, and drain come up inside the footprint. The connections do not need to cross the doorway. From the center, supply lines and wiring can go upward, outward, and into accessible routes around the shell. Drainage stays down at the floor.",
        "You can change the rooms around that known service location instead of redesigning the whole house every time your life changes.",
    ), "byod_rooms", (90., 57., 19.)),
    chapter("rooms", "Your life changes. The rooms can too.", "Bedroom + office. Later, a larger bedroom.", (
        "Split a big bedroom to make an office. Three years later you retire, stop needing the office, and open the bedroom back up.",
        "I live in a trailer. Four bedrooms, living room, den, office, two bathrooms, kitchen, dining area. We have all the allotments of a domicile. But the way we need that space has changed.",
        "I was gone for six years. I came back. Three people becomes four, and eventually that same house could be too much for one person.",
        "A dome with movable, nonstructural partitions gives us a way to reallocate the space. The shell stays. The room plan can change.",
    ), "byod_rooms", (90., 57., 19.)),
    chapter("iris", "One pad. More than one dome size.", "An iris, with leaves you can actually see move.", (
        "So what is a pad? Start with the ground, then a deck or prepared surface, and an acceptor rim that the dome latches to.",
        "The basic rim can be fixed. This upgrade is an iris: leaves moving on a track, opening and closing like a camera aperture. Watch the contact points move inward, then outward.",
        "The concept spans roughly twenty to forty feet. The deck stays in place while the acceptor changes size. A host could accommodate several dome sizes with one adjustable assembly.",
        "That mechanism is a development concept, and it belongs in the upgrade column.",
    ), "byod_iris", (90., 63., 23.), duration=22),
    chapter("rotation", "The deluxe version", "Turn toward the sun. Or choose a different view.", (
        "Then there is the top-line version: a rotating foundation. This is the expensive one. And honestly, it is just freaking cool.",
        "Maybe today I want the window facing the street. Maybe I have someone over and want it facing the private, fenced corner instead.",
        "Maybe I want the morning sun on my face. Maybe tomorrow I definitely do not. You could change the way the house faces even without a single solar panel.",
        "With an asymmetric solar layout, turning also gives you a way to aim that part of the shell. The bearing, drive, and rotating utility connections need their own development. This is future deluxe hardware.",
    ), "byod_rotation", (76., 30., 22.)),
    chapter("channels", "The wedge dome's service channels", "Up the center. Along the shell. Out of the way.", (
        "Here is the wedge build with its points facing outward. The paired members leave a channel along the seams, and those seams connect around the shell.",
        "Supply pipes and wiring could run up from the center, then follow accessible channels along the outside skin. Latched in place, out of the way, and still reachable when something changes.",
        "Now my dome is looking like a Brainiac build. That fits. The first one was the Frankendome, a conglomerate of different strut types. Apparently I have a theme.",
    ), "byod_channels", (65., 24., 18.)),
    chapter("panel_lip", "A place for the panels to seat", "The outward wedge leaves a tapered opening.", (
        "The same orientation also gives the panel opening a taper. A slanted edge on a face panel seats against that shape, with a lip to stop it falling through.",
        "That is the direction I want to take the frame: removable panels, accessible channels, and attachments that can be improved without throwing the skeleton away.",
    ), "byod_lip", (72., 25., 21.)),
    chapter("floor", "The pad is the floor", "Bring your home. Bring your carpet if you want it.", (
        "The arriving dome does not bring a second foundation. The deck it lands on is the deck it lives on. Services come through the middle, with an optional utility column for a sink, shower, toilet, and outlets.",
        "Bringing the carpet is up to the dome owner. I would. I love carpet. Some people want a garage-shop floor in their house. I have seen it. It works.",
        "When the home leaves, the reusable pad remains for the next one.",
        "We already see dome rentals, often glorified tents rented a weekend at a time. But own your glorified tent and rent the place to put it, and now both sides have a reason to make a long-term arrangement work.",
        "Renting a house has never felt like a way forward to me. A dome is my way out. If I can bring people along with me, that is the point.",
    ), "dp_landing", (36., 22., 29.)),
    worksheet("starter", "Start with the cheapest working version", "A small serviced deck, before the deluxe extras.", (
        "Before the fancy foundation, calculate the starting point. A small framed deck on precast blocks. A fixed rim. One shared power panel and water manifold serving four pads, with a short spur to each.",
        "Here is the calculation, line by line, using the current model's working prices. I have kept a site allowance in it, because roads, trunk services, and drainage do not become free just because four people share them.",
        "That puts this version above my ten thousand dollar target. It tells me where the design work has to go. It does not justify pretending the difference is gone.",
    ), facts.steps_starter()),
    worksheet("target", "What would a ten-thousand-dollar pad return?", "The target, tested at three proposed rents.", (
        "If I can build a complete serviced pad around ten thousand dollars, what happens at five hundred, a thousand, or fifteen hundred a month?",
        "This screen applies the model's occupancy, management, tax, and insurance allowances. At the high end, the target can pay back inside a year. At the low end it takes longer.",
        "That is conditional arithmetic. I still have to achieve the build cost and the rent, cover the remaining operating costs, and prove the pad's durability. My aim is infrastructure that serves for ten years and beyond.",
    ), facts.steps_target()),
    chapter("host_scope", "What the host maintains", "The pad and the services. A shorter repair list.", (
        "Look at the host's list: deck, rim, connections, perhaps a meter, perhaps a utility column. Weather and ordinary wear still matter.",
        "But there is no tenant-owned kitchen for the host to replace, no sofa to reupholster, and no houseful of furnishings to renew at every turnover.",
        "That is the passive-income appeal: a smaller maintenance scope and a longer stay, so the work is concentrated in the infrastructure.",
        "Utility metering can be a feature. So can shared off-grid power and water storage serving a cluster. Those are options. The basic income is the pad lease.",
    ), "byod_starter", (50., 35., 18.)),
    worksheet("operating", "The comparison a host actually makes", "Fewer recurring household costs.", (
        "If the alternative is an existing furnished short let, compare the ongoing bills. The model carries the same base management, tax, and insurance allowance on both sides.",
        "The short let adds turnover cleaning, a damage reserve, platform fees, and renovation. That is the recurring work a pad host is trying to avoid.",
        "This comparison assumes the rental building already exists. Furnishing an existing place is not the same as buying or building a new one.",
    ), operating_steps()),
    worksheet("deluxe", "Now show the deluxe price", "Rotation, adjustable iris, utility column, and solar.", (
        "Now bring back the deluxe pad: larger concrete deck, rotating base, plumbing column, and an array. Add the adjustable iris separately, because it is another mechanism with another bill.",
        "This costs much more than the starter. It can also cost more than furnishing an existing rental. That is a comparison between different starting points and different feature sets.",
        "The basic case is a floor and services. A house that turns toward a sunrise is a future option, not the minimum ticket into this system.",
    ), facts.steps_deluxe(), "dp_pad_detail", (30., 42., 28.)),
    chapter("host_design", "The work I want to do", "Design the pads. Make the next site repeatable.", (
        "I see my role becoming pad design and getting hosts started. A repeatable foundation and connection standard, with room for hosts to offer different features.",
        "Floor heating, water storage, deep freezer storage, a concrete shop floor, rotation, sun tracking, and eventually smart-system brains. Those can become development branches.",
        "The first job is to make the simple version work well enough that another host can build it from a clear plan.",
    ), "dp_pad_build", (32., 42., 25.)),
    chapter("foundation", "The part you can leave to the site", "The same home. A different arrangement underneath.", (
        "On the left is a dome standing on its own foundation. On the right, a home placed on a serviced pad, with its separate foundation removed because the site already provides it.",
        "The pad is doing a job you would otherwise have to arrange yourself. That is what lets the portable home concentrate on the parts you can keep and carry.",
    ), "dp_foundation", (90., 24., 35.)),
    worksheet("stay", "What a stay costs", "One model. Utilities included on every line.", (
        "Here is the comparison a person actually makes: hotel, short let, apartment, or your own dome on a pad. These are working scenarios, with power and water included on every line.",
        "The dome carries upkeep and the cost of tying up money in the house. It also takes a fifteen percent secondhand haircut in this model. You might build your dream home, but only you value every personal choice at the full price you paid.",
        "Under these inputs, the dome is cheaper over a year, and you still own it. Change the local rates, and the answer can change too.",
    ), steps_stay(), "dp_landing", (40., 20., 28.)),
    worksheet("crossover", "Too long to be a guest", "Too uncertain to sign for a year.", (
        "Run the same options over different stay lengths, and find the point where ownership starts making sense under those inputs.",
        "Nobody should buy and move a home just to stay somewhere for a month. A hotel or short let can be exactly the right answer.",
        "I am aiming for people who need a place for a while: too long to be a guest, too uncertain to sign for a year. That gap is the whole reason for this system.",
    ), steps_crossover(), "dp_landing", (34., 20., 27.)),
    chapter("my_story", "What this would have meant to me", "A stable home before the next big step.", (
        "When I was nineteen, I could borrow five grand against my name for college. I blew that opportunity, joined the military, and now at thirty-two I am back for revenge. Constructive revenge, apparently involving domes.",
        "I did not fail because I was stupid. My living situation was unstable. I did not have the support I needed, and I could not focus on what mattered. It cost me tremendously.",
        "What would a small home I owned have done for my eighteen-year-old self? I think it would have been revolutionary. That is the person I keep in mind when I design this.",
    ), "byod_rooms", (90., 57., 19.)),
    chapter("little_guy", "Built with the little guy in mind", "Students. Single parents. New families. People starting over.", (
        "Rich people will find ways to have what they want. I want to make a difference for the little guy: single mothers, people with limited money, starting families, bachelors, and people trying to get stable.",
        "My mother was a poor single parent. She worked so much that I went to both the before-school program and the after-school program. I wish she had had an economical home system that worked for her, instead of one more thing consuming her life.",
        "If there are women with the means to fund something like this, that is who I would especially love to reach. Help me build the kind of stability my mother deserved.",
        "I would love to become successful enough to give domes away. Maybe by then I am making dome furniture too. That is an ambition. The first step is a home people can afford to start with and improve.",
    ), "byod_rooms", (90., 57., 19.)),
    chapter("move", "Semi-nomadic", "Move when it is worth the effort.", (
        "Semi-nomadic means a house that comes apart, not a caravan you tow away on a whim. My working estimate is two days at the quick end, up to two weeks for something large or heavily layered.",
        "That is a burst of work: disassemble, transport, reassemble, connect. You spend that effort when a move is worth it. The rest of the time, you are living in a house.",
        "A different park, city, or state becomes possible without leaving the house behind. Site agreements still matter, but the improvements to your home travel with you.",
    ), "byod_departure", (88., 24., 34.)),
    worksheet("hardware", "The same design, scaled", "Part counts stay fixed. Materials grow with the house.", (
        "Take this design and change only its radius. The small version is about three hundred square feet. The largest here is about two thousand.",
        "The model keeps the same counts of struts, hubs, and panels. Its hardware bill stays the same, while the stick lengths and skin area grow.",
        "That illustrates the opportunity. It does not prove a connector rated for the small house can hold up the large one. The hardware has to be qualified for the whole intended size and load range first.",
    ), steps_hardware(), "dp_hardware", (86., 20., 54.)),
    worksheet("growth", "Buy for the next two steps", "Keep the hardware. Collect the longer members.", (
        "For my wedge system, the plan is to start with a six-foot long member, then move to ten feet, then twelve: roughly twelve hundred square feet at that final target size.",
        "This is the one hundred and twenty member wedge frame, a different layout from the catalogue example we just scaled. Keep the qualified connectors and gradually collect the longer pieces for the next build.",
        "The skin, insulation, and available pad area have to grow too. Go beyond the planned span and we may change the hardware or increase the dome frequency.",
        "That is why I would put money into a good hardware set. It should remain useful across a planned range of builds.",
    ), facts.steps_growth(), "byod_growth", (82., 24., 32.)),
    chapter("layers", "A lesson from the Arctic", "Layers under a removable weather shell.", (
        "Some of my own practices make their way into these domes. I stood lookout outside the skin of a ship in the Arctic Circle, for hours at a time, over months.",
        "Layers on layers on layers, then a wind-breaking, watertight suit over the whole thing. You look like the Michelin man. You also stay alive. Okay, it was not that dramatic every day.",
        "A removable dome shell lets us think similarly: lift the shell, add a suitable quilted layer, potentially using recycled fabric, and put the weather shell back over it.",
        "The insulation does not have to stay at whatever level you could afford on the day you built the house.",
    ), "byod_layers", (34., 24., 29.)),
    worksheet("r_value", "Improve it over time", "Add insulation when you are ready.", (
        "Here is the model's R-value ladder. Each suitable layer adds thermal resistance, reducing heat transfer through that part of the envelope.",
        "The improvement comes from adding the layer, not from the house getting older. You can keep improving heating and cooling performance as you can afford to upgrade.",
        "The outer shell still has a separate job: manage weather and wind. A real assembly needs to handle moisture and fire as well. The point is the ability to improve it, rather than treating the first build as the final one.",
    ), facts.steps_layers(), "byod_layers", (38., 23., 31.)),
    chapter("solar", "How much shell can carry solar?", "One side. Top half. Whole shell.", (
        "For solar, compare the same twenty-foot-wide dome three ways. Cells on one side. Cells on the top half with a metal skirt below. Or cells over the whole shell.",
        "The one-sided version gives rotation the clearest purpose: turn the useful face toward the sun. Whole-shell coverage means some cells face many different directions, so panel area alone cannot tell you the day's energy output.",
        "The metal skirt is also a possible rain-catching surface. The choice is about how you want to use the shell.",
    ), "byod_solar", (90., 27., 32.)),
    worksheet("solar_range", "The size sets a limit", "Capacity from panel area. Output depends on the site.", (
        "Here are the relative capacities, using the measured face area and the model's declared panel density. No panels means zero. The chosen layouts run from about five to ten kilowatts of nameplate capacity on this size dome.",
        "Those are installed-capacity figures, not a promise of energy from every curved face. Sun angle, shading, weather, and electrical losses determine production.",
        "A larger shell has more area to work with. A communal site could plan around shared demand and storage. That is a useful reason for some hosts to develop a shared energy system.",
    ), facts.steps_solar(), "byod_solar", (90., 27., 42.)),
    chapter("shared", "What a site can share", "A bathhouse. A utility core. A choice of services.", (
        "Some hosts can build around communal services. A bathhouse means a small dome may not need its own bathroom. An on-pad utility column is another option: sink, shower, toilet, outlets, and drain at the known connection point.",
        "Metered utility resale is optional. Passing through the cost is another approach. A shared off-grid plant with central storage is a more ambitious version.",
        "The useful competition between sites is their location, price, services, and how well the arrangement works for the people living there.",
    ), "dp_shared", (90., 25., 34.)),
    chapter("storage", "Another possible use", "A climate-controlled storage dome.", (
        "A side thought: I can also imagine these as air-conditioned storage buildings. A compact shell, suitable insulation, and a reusable pad could make an interesting storage system.",
        "It would need its own performance and cost check, but housing is not the only use for the same kit of parts.",
    )),
    chapter("network", "Why a network matters", "More places to go. More people who can use the system.", (
        "The closest comparison is an RV park, with a longer clock. Dome moves take work, so this is aimed at seasons and years rather than a constant stream of overnight stops.",
        "One host is a beginning. A second, a third, and eventually hundreds give the dome owner choices and give hosts a pool of residents beyond whoever happens to be in town.",
        "That network could also make resale easier. A house you can sell is an asset. A house nobody wants to buy is an expensive tent. I want to build demand for the actual system, not assume it already exists.",
    ), "dp_network", (84., 30., 66.)),
    worksheet("ask", "Small scale. Small risk.", "Prove a small site, then make it repeatable.", (
        "The goal is a hundred thousand dollars. The land and somewhere to work are already mine, so the campaign can focus on the next practical steps.",
        "One to three pads as a test group, and one to three dome designs built and measured. Develop the pad architecture so the next site starts with a plan and a cut list, instead of another invention.",
        "Most of the work is modular design and the means to do it: woodworking and metalworking, CNC plasma, three-D printers, a router or mill, casting materials, and the tools to panelize the frame I already have.",
        "Then the web app, hosting, documentation, a camera, and real promotion. I want this idea to spread like the flu, instead of sitting in a repository.",
        "This is a small pilot, not a claim that all the engineering is finished. The rotating tracking foundation stays outside this first campaign's funded scope. I intend to develop it later.",
    ), steps_ask(), "dp_site", (80., 20., 40.)),
    chapter("rewards", "What supporters get", "Founder status. A signed book. Help shaping your own build.", (
        "What do people get? The entry-level ideas are founder status on an online account, a three-D printed dome keychain or mirror hanger, a window decal, and a poster.",
        "A middle tier includes a signed book that goes alongside this codebase, the campaign, and the whole dome approach.",
        "At a higher tier, work with me to imagine your own dome, build it digitally, and form a game plan. That could be a future pad host, a dome owner, or somebody collecting possibilities for later.",
        "Those are the proposed reward categories. The campaign will set the actual tiers and delivery scope.",
    ), "byod_rewards", (90., 25., 24.)),
    chapter("close", "Bring your own dome", "Keep the value of the home you improve.", (
        "A hotel sells you a night. A short let sells you a few weeks. A lease sells you a year. I want another option: live somewhere for a while, without handing over every improvement you make to somebody else's building.",
        "Bring your own home. Pay the host for the ground and services. Improve your house because it is your house, then take those improvements with you.",
        "The source, the model inputs, and the experiments should be open. Actual open source, not just a marketing word. The drawings, the prices, and the things that fail should all be available to check.",
        "And if this campaign does not fund, my plan and my work are the same. I am building this whether it takes one year or ten. Support changes the speed and how many people the work reaches along the way.",
    )),
    chapter("share", "One person who can carry it further", "Send this to someone who should see it.", (
        "If this was worth your time, send it to one person who can carry it further than I can.",
        "A share from somebody with reach can do more for this than a month of me in a field with a chainsaw. That is the ask. Help the idea reach the people who could build it, host it, or need it.",
    )),
    *OUTRO.chapters,
)

CHAPTERS = tuple(replace(c, number=f"{i + 1:02d}") for i, c in enumerate(CHAPTERS))


def scene_lip(app, opaque, transparent, p):
    from .lesson_wedge_why import scene_ww_keystone
    scene_ww_keystone(app, opaque, transparent, p)


SCENES = {**old.SCENES, **NEW_SCENES, "byod_lip": scene_lip, **OUTRO.scenes}


def validate_byod():
    facts.validate()
    BYOD_LESSON.validate()
    assert CHAPTERS[0].promise == "BRING YOUR OWN DOME"
    assert CHAPTERS[0].overlay == "title"
    assert len({c.slug for c in CHAPTERS}) == len(CHAPTERS)
    assert iris_radius(1) > iris_radius(0) * 1.9
    assert next(i for i, c in enumerate(CHAPTERS) if c.slug == "starter") < next(i for i, c in enumerate(CHAPTERS) if c.slug == "deluxe")
    from .raw_wedge_bridge import model
    assert len(model("point_dome_out").members) == 120
    for c in CHAPTERS:
        for p in (0., .5, 1.):
            probe = old._Probe(c.overlay, c.camera)
            a, b = TriangleBatch(), TriangleBatch()
            SCENES[c.stage](probe, a, b, p)
            assert a.vertices or b.vertices or probe.creator_draws, (c.slug, p)
            for batch in (a, b):
                assert np.isfinite(batch.vertices).all(), (c.slug, p)
            assert all(x.build.triangles > 0 for x in probe.creator_draws)
    for slug in ("layers", "r_value"):
        c = next(c for c in CHAPTERS if c.slug == slug)
        probe = old._Probe(c.overlay, c.camera)
        SCENES[c.stage](probe, TriangleBatch(), TriangleBatch(), 1.)
        assert not any("$" in x.text or "pay" in x.text.lower() for x in probe.world_labels)


BYOD_LESSON = Lesson(
    key="byod", brand="BRING YOUR OWN DOME", title="Bring Your Own Dome",
    chapters=CHAPTERS, scenes=SCENES, selftest=validate_byod,
    report=facts.report, snapshot_prefix="byod", style="hype", voice_rate="+2%",
    label_layout="declutter", ground="off", frame_fit="off",
)
