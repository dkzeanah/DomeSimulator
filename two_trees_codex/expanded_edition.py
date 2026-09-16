"""Reviewed image-to-passage plan for the expanded Codex reading edition."""
from __future__ import annotations

import json
from pathlib import Path

from .illustrate import apply_illustration_plan
from .storage import BookStore, new_page, stamp


def main():
    store = BookStore()
    root = store.home / 'expanded-art'
    videos = json.loads((root / 'video-curated-20260912T104321107815Z/manifest.json').read_text(encoding='utf-8'))
    native = json.loads((root / 'native-tools-selected-20260912T1041.json').read_text(encoding='utf-8'))
    video = {v['id']: v for v in videos['results']}
    pages = {p['id']: p for p in store.book['pages']}
    additions = [
        ('codex-jig', 'codex-fixture-sequence', 'Plate sequence — From layout to loaded fixture',
         "Dome Forge separates a fixture into visible stages: the reference layout, the locating fences, and the loaded frame. Compare the stages in that order. The unchanged datum explains what the next piece is being located against.\n\nThese native tool views use Forge's mitered board-frame demonstration. They illustrate registration and repeatability. The raw-wedge pinwheel in this book has its own butt-to-side contact surfaces and must be laid out from that configuration.\n\nThe compound-cut film supplies another reference example: a stop block, relief lap, and fence. Its visible angle and allowance labels belong to its source setup. Carry the principle of a documented datum into the wedge trial; derive the actual contact and cut from the selected wedge model.\n"),
        ('codex-from-frame-home', 'codex-enclosure-sequence', 'Plate sequence — The work beyond the frame',
         "Assembly Line makes later work visible as separate stations. These clean native renders show services, insulation, and interior work around its factory dome. The changing layers help explain why a bare frame and an inhabitable enclosure are different milestones.\n\nThis is the Assembly Line model's 3V production example. Its geometry, quantities, crew, and station times are separate from the book's 2V, forty-panel experiment. Use the sequence to ask what work remains and what interfaces must stay accessible.\n\nFollow a service through the enclosure, then examine the insulation and interior layers. Record where the real design will provide access, manage moisture, and meet its performance requirements. These are modeled stages, not photographs documenting completion of the two-tree build.\n"),
        ('codex-project-atlas', 'codex-dome-world-gallery', 'Gallery — Other destinations in Dome World',
         "The existing Dome World presentation uses a common visual language to compare very different destinations: a greenhouse, an elevated canopy, and a whole-trunk lodge. The three stills retain the source presentation's model and labels.\n\nThe greenhouse changes the frame material and skin. The elevated canopy adds a supporting platform. The lodge starts with far longer whole-trunk members. Each choice changes the material schedule and the questions the design must answer.\n\nTheir displayed dimensions, costs, areas, and member counts belong to those individual source configurations. They are examples of the wider design space, not alternate views of a house made from this book's 120 wedge members.\n"),
    ]
    for after, key, title, body in additions:
        if key in pages:
            continue
        page = new_page(title, 'plate', 'explanation', body)
        page['id'] = key
        index = next(i for i, p in enumerate(store.book['pages']) if p['id'] == after)
        store.book['pages'].insert(index + 1, page)
        pages[key] = page

    plan = {'schema': 'two-trees-illustration-plan/v1', 'id': 'expanded-reading-edition-20260912', 'illustrations': []}

    def add(result, key, page, paragraph, caption, family):
        plan['illustrations'].append(dict(id=key, page_id='codex-' + page, result=result,
            caption=caption, after_paragraph=paragraph, source_family=family,
            purpose=result.get('purpose', result.get('recipe', {}).get('purpose', ''))))

    def film(key, page, paragraph, caption, family='Video engine presentations'):
        add(video['video-' + key], 'video-' + key, page, paragraph, caption, family)

    film('v1-13', 'first-question', 4, 'A possible destination, still on screen: Dome World renders a timber workshop. This 3V example has its own member count, area, and cost assumptions. It shows the ambition behind the opening question, not the completed two-tree frame.', 'Dome World presentation')
    film('v2-11', 'frankendome', 1, 'The Frankendome presentation starts with unlike stock profiles: square, wedge, quarter-sawn, and round. The repeated interface was the question that carried into the later wedge-frame study.')
    film('v2-12', 'frankendome', 2, 'The earlier V bracket joins two members. Its screw count and bracket geometry belong to that Frankendome example; the later wedge pinwheel develops a different physical corner.')
    film('v2-01', 'discovery', 1, 'One radial sector becomes a long member while keeping its two radial faces and curved outside. The presentation isolates the profile so the change from trunk to wedge can be seen.')
    film('v3-02', 'scope', 2, 'The existing film separates measured observations from estimates in its math panel. Use that same separation in the experiment ledger: a source calculation is not a completed-build measurement.')
    film('v3-03', 'scope', 4, 'Two cutting observations in the source film use different units: wedges produced in a session and feet of ripping in another. Preserve elapsed time, fuel, and the counted operation together before comparing rates.')
    film('v2-07', 'mesh', 1, 'The parent icosahedron supplies twelve vertex directions. The source presentation uses the golden ratio to locate those directions before subdivision; it is not a ratio to apply directly to the finished strut lengths.')
    film('v1-22', 'mesh', 2, 'After subdivision, the new points are projected radially to the sphere. Straight chords reconnect the projected points. This is the geometric step that creates the dome mesh.')
    film('v1-03', 'counts', 2, 'Forty independent triangular frames form the shell. Each triangle owns three wooden members, so a shared boundary contains the two members brought by its neighboring panels: 40 × 3 = 120.')
    film('v2-08', 'radius-method', 2, 'The source presentation colors the two chord families after projection. In this book, long A = 0.618033989R and short B = 0.546533058R; physical wedge blanks still require the joint and allowance calculation.')
    film('v2-09', 'radius-example', 1, 'The radius-first derivation is held as a still. At R = 120 inches, the book\'s nominal long chord is about 74.164 inches and its short chord about 65.584 inches. These are geometric chords, not a final saw schedule.')
    film('v2-10', 'radius-example', 3, 'The reference hemisphere is organized into rings and a crown. A spherical radius, a polygonal base, and a vertical ring height describe different dimensions; retain their labels when comparing the worked example.')
    film('v1-11', 'tree-method', 5, 'The earlier film lets its available stock length control the radius. Its on-screen dimensions belong to that source setup. For this book, solve the physical member envelope against the measured usable blank, then verify the resulting radius.')
    film('v1-10', 'tree-ledger', 4, 'The inventory becomes forty separately made frames. Count source blanks, accepted members, and accepted panels in separate ledger columns so the same piece of timber is not counted twice.')
    film('v2-03', 'radial-wood', 1, 'The radial split opens the circular cross-section into eight 45-degree sectors. The separated pieces show the ideal geometry; the actual yield must also include ripping kerf, defects, taper, and end trimming.')
    film('v3-01', 'read-tree', 2, 'A defect in the source presentation interrupts a long member. Dividing the stock into shorter assigned pieces can isolate a loss, but each retained piece must still qualify for its intended member.')
    film('v1-01', 'recovery', 4, 'The existing timber comparison places rectangular boards and radial wedges inside the same round outline. It explains where packing losses arise. The final recovery comparison must use measured inputs and the same definition of useful output.')
    film('v2-16', 'green-wood', 2, 'The source model compares members from different trunk diameters around a panel. This is stock variation, not a simulation of drying. Use it to identify the section dimensions and contact surfaces to remeasure on documented samples over time.')
    film('v1-17', 'work-sequence', 2, 'Assembly Line separates the stockpile, work station, and the path between them. That spatial view makes material handling visible in the work plan. The depicted crew and production setting belong to the source factory example.', 'Assembly Line presentation')
    film('v1-18', 'work-sequence', 4, 'The source presentation breaks one placed part into walking, lifting, carrying, positioning, fastening, and recovery. Its durations and energy estimates are model values; record the actual operation and elapsed labor in the two-tree log.', 'Assembly Line presentation')
    film('v1-05', 'wedge-orientations', 3, 'Four orientations of the same wedge are held side by side. Follow the sector point first, then inspect the two members at a panel boundary. Changing orientation changes the physical seam while leaving the ideal edge family unchanged.')
    film('v2-02', 'joint-geometry', 1, 'The pinwheel runs cyclically: the butt of each member meets the side of the next member near its head. Three separate members remain in the triangle. A neighboring triangle brings its own member to the shared axis; this is not a single-stick lattice.')
    film('v1-07', 'jig', 1, 'The source fixture scene holds a triangular frame against stops while the final member enters. The important relationship is between the member contact, the reference layout, and the stop surfaces; its exact dimensions remain specific to that source model.')
    film('v1-08', 'panel-production', 2, 'A reference fence and deliberately overlong stock make the repeated contact visible. The film illustrates how a fixture can transfer a checked relationship to the next panel; the book\'s actual trimming allowance belongs in the member record.')
    film('v1-28', 'fixture-sequence', 3, 'The compound-cut presentation isolates its stop block, relief lap, and fence. This is a separate fixture configuration. Use it to understand registration and clearance, then derive the raw-wedge fixture from the selected contact geometry.')
    film('v1-06', 'seams', 3, 'The colored seam network continues across the shell. It makes a possible continuous path visible, while the book\'s two-panel trial must establish the real contact, fastener space, and weather detail.')
    film('v2-13', 'base', 3, 'The earlier Frankendome deck is shown above its supports. It illustrates why a frame needs a defined base and load path. Its deck dimensions and support count are source examples, not the foundation design for this build.')
    film('v1-25', 'raising', 2, 'The source film exposes successive courses instead of hiding the incomplete frame inside a finished shell. Use the staged view to identify panels and reference nodes. Actual temporary support and assembly order require the plan for the chosen build.')
    film('v1-19', 'raising', 4, 'Assembly Line isolates lifting and positioning as work of their own. This modeled motion explains why handling belongs in the assembly plan; its body model and energy numbers do not specify a safe lifting procedure.', 'Assembly Line presentation')
    film('v1-27', 'from-frame-home', 3, 'The presentation connects a roof catchment to storage. Its annual water label depends on its source area and rainfall assumptions. Here the image introduces the enclosure and drainage questions that remain after the frame is assembled.')
    film('v2-18', 'fortnight-plan', 2, 'The longest modeled station time sets the source production line\'s pace. For the fortnight plan, look for the corresponding constraint in actual records: a fixture adjustment, inspection queue, material move, or unresolved panel can control progress.', 'Assembly Line presentation')
    film('v2-17', 'economics', 2, 'The source presentation compares the operations between a tree and a finished member. A proposed omitted operation is a question for the ledger: count the replacement work, equipment, consumables, and accepted product before assigning a saving.')
    film('v1-20', 'economics', 3, 'A modeled work breakdown makes fastening, carrying, lifting, and other motions visible. These are the Assembly Line film\'s estimates. The two-tree comparison needs measured labor from setup through accepted output.', 'Assembly Line presentation')
    film('v2-14', 'project-atlas', 2, 'A hexagonal dome cage from the existing masterclass. The tool makes another topology visible; its faces, joints, and member inventory differ from the forty-triangle hemisphere in this book.')
    film('v2-15', 'project-atlas', 3, 'The zome masterclass shows a shell rising through level tiers. This is a different geometric family. Keep its sequence and part count with its own model when using it as a visual comparison.')
    film('v1-15', 'dome-world-gallery', 1, 'Dome World\'s greenhouse configuration pairs a modeled frame with translucent panels. Its 3V subdivision, materials, area, and cost assumptions belong to this source example.', 'Dome World presentation')
    film('v1-16', 'dome-world-gallery', 2, 'The elevated canopy configuration introduces a separate support platform beneath the dome. Its displayed member count describes the source frame, not all timber and connections in a complete supported structure.', 'Dome World presentation')
    film('v2-05', 'dome-world-gallery', 3, 'The whole-trunk lodge explores a much larger shell with long whole-trunk members. Its scale helps show why a common geometric idea can lead to a different harvest, handling plan, and material schedule.', 'Dome World presentation')

    native_places = [
        (0, 'mesh', 5, None),
        (1, 'counts', 4, None),
        (2, 'fixture-sequence', 2, None),
        (3, 'fixture-sequence', 1, None),
        (4, 'fixture-sequence', 2, None),
        (5, 'radial-wood', 4, 'Dome Forge compares a panel made with half-round, rectangular, and quarter-round members around an infill. These profiles illustrate how stock shape changes the occupied boundary. They are different from the book\'s uniform eighth-sector wedge.'),
        (6, 'ending', 1, 'Dome Forge renders a split-log shell as a possible outcome of a panel system. Its mixed half-round and quarter-round members are a modeled design variant. The closing chapter must still be completed with the actual two-tree inventory, configuration, and field photographs.'),
        (7, 'from-frame-home', 3, None),
        (8, 'base', 1, None),
        (9, 'panel-production', 6, None),
        (10, 'enclosure-sequence', 1, None),
        (11, 'enclosure-sequence', 2, None),
        (12, 'enclosure-sequence', 3, None),
        (13, 'from-frame-home', 5, None),
    ]
    for i, page, paragraph, caption in native_places:
        result = native['assets'][i]
        add(result, 'native-' + Path(result['path']).stem, page, paragraph,
            caption or result['caption'], result['recipe']['tool'])

    assert len(plan['illustrations']) == 52
    path = root / ('book-illustration-plan-' + stamp() + '.json')
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    report = apply_illustration_plan(store, plan)
    report['plan'] = str(path)
    report_path = store.write_export('illustration-coverage', '.json', json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != 'pages'}, indent=2))
    print('Coverage report:', report_path)


if __name__ == '__main__':
    main()
