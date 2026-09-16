; ============================================================================
; Facebook description paste revolver - DomeSim video uploads (BATCH MODE)
;
; F9        AUTO-BATCH: asks HOW MANY videos to fill, then how many TAB
;           presses it takes to reach the NEXT video's description field
;           (the tab count is remembered between runs). Focus the FIRST
;           video's description field, confirm, and for each video it does:
;             Ctrl+A  (select whatever is already in the field)
;             copy the description to the clipboard
;             Ctrl+V  (paste)
;             Tab xN  (jump to the next description field)
;             Ctrl+A  (select that next field's content, ready for the next paste)
;           Each field gets a DIFFERENT SEO variation + 5 random hashtags.
;
; F7 / F8   change the tab count LIVE (down / up) - shown in the tooltip.
;           If focus drifts mid-batch, adjust and the next fields follow.
; Ctrl+F12  abort the running batch (stops after the current field).
; Ctrl+F9   single step: paste ONE generic description (current index).
; F10/F11/F12  manual index back / preview / reset.
; Ctrl+F11  dump all 50 generic descriptions to descriptions_dump.txt.
;
; The tab count and manual index survive restarts (files beside the script).
; If the uploader is slow, raise FIELD_SETTLE below; if focus lands on the
; page instead of the next field, the tab count is wrong for your dialog -
; lower F7 / raise F8 until Ctrl+A selects text inside the box, not the page.
; ============================================================================

#Requires AutoHotkey v2.0
#SingleInstance Force
#MaxThreadsPerHotkey 1

stateFile := A_ScriptDir "\revolver_state.txt"
tabsFile := A_ScriptDir "\revolver_tabs.txt"

PASTE_SETTLE := 500    ; ms to wait after each paste
FIELD_SETTLE := 1500   ; ms to wait after tabbing, for the next field to focus

batchStop := false
tabCount := 4          ; Tab presses between description fields (F7/F8 adjust)

if FileExist(tabsFile) {
    try {
        savedTabs := Integer(FileRead(tabsFile))
        if (savedTabs >= 0 and savedTabs <= 40)
            tabCount := savedTabs
    }
}

; ---------------------------------------------------------------------------
; Hashtags: 5 per video, picked at RANDOM from this pool at paste time, so
; every one of the 50 fields gets its own fresh combination. Facebook has
; no hard hashtag cap; 5 is the safe, clean number. Add or remove pool
; entries freely - each pasted description always gets exactly 5.
; ---------------------------------------------------------------------------

hashtags := ["#math", "#geodesicdome", "#dome", "#tinyhouse", "#homesteading",
             "#diy", "#fyp", "#economics", "#home", "#sawmill", "#chainsaw",
             "#lumber", "#wood", "#pinetree"]

HashtagTail() {
    global hashtags
    pool := []
    for tag in hashtags
        pool.Push(tag)
    tail := ""
    Loop 5 {
        pick := Random(1, pool.Length)
        tail .= pool[pick] " "
        pool.RemoveAt(pick)
    }
    return RTrim(tail)
}

; Final text for one video: the description's prose (its plain-text keyword
; line is dropped - the hashtags carry that job now) plus 5 random hashtags.
FinalText(base) {
    prose := RegExReplace(base, " [^.]*\|[^.]*$", "")
    return prose . "`n`n" . HashtagTail()
}

; ---------------------------------------------------------------------------
; 50 SEO variations of ONE generic message: this is a code-generated video
; library that promotes, advances, develops, and masters geodesic dome
; construction as THE solution to America's housing crisis.
; ---------------------------------------------------------------------------

descriptions := [
"Code-generated 3D explainer series - small discrepancies are probable, but every number on screen is computed by code that proves itself. These videos promote, advance, develop, and master geodesic dome construction as THE solution to America's housing crisis: forty triangles, two strut lengths, two jigs, and a roof that shares its load instead of stacking it. Geodesic dome construction | how to build a geodesic dome | dome home | affordable housing crisis solution | DIY dome building",
"Watch a geodesic dome go from raw math to a raised frame in this code-generated masterclass library - discrepancies are probable, the geometry is not. Step-by-step geodesic dome construction, hub-and-strut and hubless framing, cut lists, jigs, and raising rings, all promoting, advancing, developing, and mastering the dome as THE answer to America's housing crisis, because two strut lengths and two jigs build the whole frame. Geodesic dome construction guide | 2V dome kit | dome framing | housing crisis America | geodesic dome tutorial",
"Programmatically generated dome-building videos - expect the occasional discrepancy, trust the arithmetic. A complete DIY geodesic dome home curriculum: geometry first, then jigs, foundations, raising, skinning, and the mistakes that actually stop domes going up. Made to promote, advance, develop, and master geodesic dome construction as THE solution to America's housing crisis: the most room for the least material, repeatable from two jigs. DIY geodesic dome | build your own dome home | geodesic dome plans | affordable alternative housing | dome construction for beginners",
"Code-generated video - discrepancies are probable. This is a deep explainer on 2V geodesic dome geometry and construction: phi placing the vertices, the two chord classes, the 30-SHORT / 35-LONG cut list, and why a ten-sided base ring amplifies a strut error by exactly phi. Every film promotes, advances, develops, and masters geodesic dome construction as THE solution to America's housing crisis - a shell that shares its load is a home that shares its cost. 2V geodesic dome | geodesic dome geometry | dome chord factors | geodesic dome cut list | housing crisis solution",
"America's housing crisis has a geometric answer, and this code-generated video library - discrepancies are probable - walks the whole argument. Geodesic dome construction explained from first principles: one sphere shape, two strut lengths, forty triangles, no bearing walls, and a price that does not check your credit. Promoting, advancing, developing, and mastering the geodesic dome as THE solution to the housing crisis: most room, least skin. Affordable housing America | geodesic dome house | alternative housing crisis | dome shelter | geodesic home construction",
"This channel is generated in code - small discrepancies are probable - and every figure is computed, never claimed. Off-grid and homestead builders will find the full geodesic dome construction path: tree to wedge to frame, or lumber to hub, with jigs, raising, and costing along the way. It exists to promote, advance, develop, and master geodesic dome construction as THE solution to America's housing crisis: two lengths of wood and two jigs put a roof over anyone. Off-grid dome home | homestead geodesic dome | DIY off-grid housing | geodesic dome frame | self build dome",
"Code-generated 3D explainers - discrepancies are probable, every number is provable. What does geodesic dome construction actually cost? Watch the costing, the material breakdown, the labor ledger, and the value ladder - then the argument that the dome is THE solution to America's housing crisis, because a 2V frame is two strut lengths, two jigs, and shared load. Geodesic dome cost | dome home price | dome materials list | building a dome cheap | housing crisis affordable homes",
"From a standing pine to a 300-square-foot shell: this code-generated video series - discrepancies are probable - shows eight cuts turning a tree into a house. Raw log wedges, pinwheel frames, gasketed seams, and no sawmill anywhere in the chain. It promotes, advances, develops, and masters geodesic dome construction as THE solution to America's housing crisis: the tree is already there, the jig is two jigs, and the frame is forty triangles. Sawmill-free building | log wedge dome | tree to house | raw timber framing | geodesic dome homestead",
"Code-generated video - discrepancies are probable - on hubless geodesic dome construction: forty separate bolted triangles, no hubs, no connectors, every seam two boards thick. The full hubless method, the compound cut, and the jigs that make it repeatable, all made to promote, advance, develop, and master geodesic dome construction as THE solution to America's housing crisis. Hubless dome | geodesic dome framing | dome triangle panels | compound cut dome | alternative housing solution",
"Every calculation between one irrational number and a lit pixel, generated in code - discrepancies are probable. Geodesic dome math and construction on screen: phi, subdivision, chord factors, projection matrices, and the cut list that falls out of one multiplication. Promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis - the geometry does not check your credit. Geodesic dome math | dome geometry calculator | geodesic geometry explained | dome chord length | housing crisis math",
"Code-generated 3D explainers - discrepancies are probable - covering geodesic dome construction for greenhouses, shelters, cabins, and full homes. The same dome math sizes a grow dome, a storm shelter, a storage shed, or a house, and this library promotes, advances, develops, and masters geodesic dome construction as THE solution to America's housing crisis: most space, least material, shared load. Geodesic dome greenhouse | dome shelter | geodesic cabin | dome shed | affordable shelter housing",
"Think of it as a tiny home with a better shape: this code-generated video library - discrepancies are probable - makes the case that the geodesic dome is the tiny house alternative that scales. Geodesic dome construction from cut list to crown, promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis: a sphere gives the most room for the least skin. Tiny home alternative | geodesic tiny house | dome tiny home | alternative living dome | housing crisis tiny homes",
"Code-generated video - discrepancies are probable - on sustainable geodesic dome construction: two strut lengths, two jigs, less material than a box, and a shell that shares every load. Solar bands, water-harvesting seams, natural cooling - the dome is built for it, and this library promotes, advances, develops, and masters geodesic dome construction as THE solution to America's housing crisis. Sustainable building dome | eco dome home | solar dome | geodesic dome energy | green housing crisis",
"One frame, two jigs, forty triangles: this code-generated series - discrepancies are probable - shows the geodesic dome construction kit that fits in a truck. Because every 2V dome is the same two shapes, the jigs are the factory, and each build is faster than the last - which is why these videos promote, advance, develop, and master the dome as THE solution to America's housing crisis. Geodesic dome kit | dome jig | repeatable dome build | geodesic dome DIY kit | prefab dome home",
"Code-generated explainers - discrepancies are probable - spanning geodesic, zome, and hexagonal dome construction: flat parallelogram panels, one strut length, twelve pentagons, and the frequency ladder. A whole family of triangulated shelters, made to promote, advance, develop, and master geodesic dome construction as THE solution to America's housing crisis. Zome construction | hexagonal dome | geodesic dome frequency | triangulated dome home | alternative housing geometry",
"Build the bones once, replace everything else for fifty years: this code-generated montage library - discrepancies are probable - is the frankendome argument. Mixed-stock struts, folded V brackets, and upgradeable skins over one geodesic skeleton, promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Frankendome | geodesic dome upgrade | mixed stock dome | dome skins | fifty year dome home",
"From fifteen gantry stations to a solar-tracking turntable: code-generated factory footage - discrepancies are probable - of geodesic dome construction on an assembly line. Per-element costs, per-station labor, and the throughput math that makes a manufactured dome home the repeatable answer - promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Dome factory | manufactured dome home | geodesic dome assembly line | prefab housing crisis | dome production line",
"Code-generated video - discrepancies are probable - on the energy of building a geodesic dome: two people, six motions per part, and the finding that fastening - which raises nothing - is ninety percent of the fuel. The dome wins because it is light: fewer parts, less lift, shared load. These films promote, advance, develop, and master geodesic dome construction as THE solution to America's housing crisis. Dome energy efficiency | geodesic dome build labor | lightweight dome frame | dome construction crew | efficient housing construction",
"Self-build housing without a mortgage on the frame: this code-generated library - discrepancies are probable - walks geodesic dome construction from the base ring to the apex for the person who will raise it themselves. Every figure recomputable, every jig buildable, promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Self build dome | DIY geodesic dome home | owner builder dome | homestead construction | housing crisis self build",
"Code-generated 3D - discrepancies are probable - on timber-frame geodesic dome construction: dimensional lumber, raw log wedges, bamboo, and steel, all through the same two jigs. Mixing sections is a geometry problem, not a paint job, and this library promotes, advances, develops, and masters geodesic dome construction as THE solution to America's housing crisis. Timber frame dome | geodesic dome lumber | log dome frame | wood dome construction | timber housing alternative",
"Software generates every frame and every number - discrepancies are probable. This is geodesic dome construction as engineering: parametric models, a live bill of materials, ray-picked panels, and a 360-degree renderer. The toolchain promotes, advances, develops, and masters the geodesic dome as THE solution to America's housing crisis: computed, not claimed. Geodesic dome software | dome design tool | parametric dome model | geodesic dome BIM | dome construction calculator",
"Code-generated video - discrepancies are probable - on the dome built straight from the tree: raw 45-degree log sectors, bark out, pith in, forty independent pinwheel frames, and gasketed seams. Eight cuts to a house, no sawmill required - promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Raw wedge dome | log sector construction | pinwheel frame dome | sawmill free home | tree to dome",
"THE solution to America's housing crisis, argued in code: this video library - discrepancies are probable - promotes, advances, develops, and masters geodesic dome construction as the answer to housing costs. Forty triangles from two strut lengths, a shared load instead of a stacked one, two jigs instead of a factory, and a price set by geometry, not by zip code. Housing crisis solution | geodesic dome housing | affordable dome homes | America housing affordability | dome construction crisis",
"New to domes? Start here: this code-generated explainer series - discrepancies are probable - teaches geodesic dome construction from absolute zero. What a 2V dome is, why two strut lengths are enough, how the triangles go together, and how a dome gets raised - promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Geodesic dome basics | what is a geodesic dome | dome for beginners | learn dome building | geodesic dome 101",
"A full geodesic dome construction masterclass, one chapter at a time: code-generated 3D - discrepancies are probable - from phi coordinates to a closed crown. Geometry lessons, construction lessons, costing lessons, and the four mistakes that stop domes going up - all promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Geodesic dome masterclass | dome construction course | dome building video | geodesic dome education | housing crisis lessons",
"Code-generated video - discrepancies are probable - on geodesic dome frequency: 1V to 4V, why odd frequencies stand taller than a hemisphere, and what more strut lengths cost. The frequency ladder decides price per square foot, and this library promotes, advances, develops, and masters geodesic dome construction as THE solution to America's housing crisis. Geodesic dome frequency | 2V 3V 4V dome | dome strut lengths | geodesic dome design | dome price per square foot",
"Every strut, panel, hub, and dollar, computed live: this code-generated series - discrepancies are probable - shows the geodesic dome bill of materials in full. Cut lists, material weights, solar kilowatts, and the trees behind a timber dome - promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Dome bill of materials | geodesic dome cut list | dome strut count | dome material cost | housing crisis materials",
"Wind, snow, seismic: the triangulated shell is the story, and this code-generated library - discrepancies are probable - tells it honestly, hedges included. Geodesic dome construction for resilient housing, with the claims these videos will NOT make - promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Geodesic dome wind resistance | dome seismic design | resilient dome home | storm proof dome | disaster housing solution",
"Code-generated 3D explainers - discrepancies are probable - on the off-grid geodesic dome: solar bands laid on the faces that really face the sun, water-harvesting seams, battery banks, and passive cooling. The dome earns its keep, and these videos promote, advance, develop, and master geodesic dome construction as THE solution to America's housing crisis. Off-grid solar dome | geodesic dome solar panels | water harvesting dome | dome power system | self sufficient dome home",
"Inside the dome: code-generated tours - discrepancies are probable - of furnished geodesic dome interiors. An open floor with no bearing walls, furniture checked against the faceted shell, and a cast of characters showing how the room works - promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Dome home interior | geodesic dome living | dome interior design | open plan dome | dome house tour",
"Code-generated video - discrepancies are probable - on the hardest cut in a hubless geodesic dome: the compound cut, on both machines, with the jig between them. The rip bevel, the sled mitre, the relief lap, and the stop block - promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Compound cut dome | hubless dome joinery | dome bevel cut | geodesic dome woodworking | dome construction joinery",
"Two strut lengths. Two jigs. Forty triangles. That is the whole factory: this code-generated library - discrepancies are probable - repeats the geodesic dome construction argument until it lands, because it is THE solution to America's housing crisis - a repeatable answer instead of a handmade miracle. Geodesic dome repeatable build | dome jig system | two strut dome | dome mass production | housing crisis repeatable homes",
"Frames that cannot lie: every picture here is generated in code - discrepancies are probable - from the same modules that compute the numbers. Geodesic dome construction rendered deterministically, promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis: what you see is what the math says. Code generated video dome | deterministic dome render | geodesic dome animation | dome 3D simulation | housing crisis visualization",
"Watch a dome rise ring by ring, cable by cable: code-generated construction simulation - discrepancies are probable - of geodesic dome raising, the measurement loop, and the crown closing true. The whole build, promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Dome raising | geodesic dome construction sequence | dome base ring | dome crown | dome assembly video",
"Code-generated video - discrepancies are probable - on the dome that drinks the rain: dished panels, micro-drains, seam veins, a collector ring, and a cistern. Water-harvesting geodesic dome construction, promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Rainwater dome | geodesic dome water system | dome gutter ring | off-grid water dome | sustainable dome home",
"The value ladder of a tree, computed not claimed: code-generated economics - discrepancies are probable - from a $20 standing pine to thousands of dollars of avoided framing. The dome is the highest use of the wood, and this library promotes, advances, develops, and masters geodesic dome construction as THE solution to America's housing crisis. Tree value ladder | dome framing value | pine to dome | dome economics | affordable framing housing",
"Code-generated explainers - discrepancies are probable - on geodesic dome construction without bearing walls: the shell carries the load, so the floor plan is free. One open room, curved walls handled, and the honest trade-offs on camera - promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Dome open floor plan | no bearing walls dome | geodesic dome interior layout | dome accessibility | housing crisis floor plans",
"A homestead build plan with the arithmetic attached: this code-generated library - discrepancies are probable - sizes the geodesic dome from the tree you have or the floor you want. Method A, method B, and the round trip that proves they agree - promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Homestead dome plan | dome sizing | tree to dome math | geodesic dome build plan | homestead housing crisis",
"Code-generated video - discrepancies are probable - from the jig shop: two jigs produce every triangle in a geodesic dome, and every figure is re-measured off the assembled 3D faces. The shop that makes the dome repeatable, promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Dome jig shop | geodesic dome jigs | triangle jig dome | dome workshop | repeatable dome construction",
"Want the numbers? Get the calculator: this code-generated series - discrepancies are probable - walks the geodesic dome construction calculator, the chord factors, and the cut list that falls out of one multiplication. Every figure recomputable, promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Geodesic dome calculator | dome chord factor | dome cut list generator | geodesic dome dimensions | housing crisis calculator",
"Precision woodworking meets geodesic geometry: code-generated close-ups - discrepancies are probable - of the miter, the bevel, the butt cut, and the jig that makes them all repeatable. Geodesic dome construction for people who cut wood for real - promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Dome miter cut | geodesic dome angles | dome butt cut | precision dome joinery | woodworking dome home",
"Code-generated 3D - discrepancies are probable - and a furnished geodesic dome lookbook: two sets, a cast of eight, hair modeled as strands, and furniture that fits against a faceted shell. The dome as a place to live, promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Dome lookbook | geodesic dome furniture | dome home design | dome cast | housing crisis living spaces",
"From phi to pixels: this code-generated masterclass - discrepancies are probable - derives the shape and then the picture of geodesic dome construction, down to the vertex buffer and the lighting sum. The whole rendering chain, promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Geodesic dome from scratch | dome geometry to pixels | dome rendering explained | 3D dome graphics | housing crisis explainer",
"Code-generated video - discrepancies are probable - on the energy ledger of geodesic dome construction: mechanical work computed limb by limb, food energy modeled motion by motion. Lighter frames, fewer lifts - the dome wins the physics, and these films promote, advance, develop, and master it as THE solution to America's housing crisis. Dome construction energy | dome labor cost | dome crew efficiency | lightweight home construction | energy efficient housing",
"Manufactured housing, but round: code-generated factory sims - discrepancies are probable - of geodesic dome homes rolling down a fifteen-station line, priced per element, stacked in a yard. The repeatable path to scale, promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Manufactured dome home | geodesic dome factory | dome housing production | prefab round house | housing crisis manufacturing",
"The square house stacks its costs; the triangle shares them: this code-generated video library - discrepancies are probable - puts the dome against the conventional box, dollar for dollar, and lets the numbers argue. Promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Dome vs square house | geodesic vs conventional home | dome house comparison | housing crisis comparison | round vs box home",
"Code-generated video - discrepancies are probable - on building a log home without a sawmill: split, quarter, eighth - one log becomes eight wedge blanks and forty triangles become a dome. The cheapest member in construction, promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Log home without sawmill | wedge log building | split log dome | chainsaw home building | affordable log dome",
"One shape, shared by a community of builders: this code-generated library - discrepancies are probable - documents geodesic dome construction as an open, repeatable method. Two jigs, two lengths, forty triangles - knowledge that ships anywhere, promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Dome community housing | geodesic dome coop | open source dome | dome building community | housing crisis movement",
"The whole toolchain, on camera: code-generated tours - discrepancies are probable - of the dome creator, the forge, the assembly line, and the video engine itself. Every tool that builds the argument, promoting, advancing, developing, and mastering geodesic dome construction as THE solution to America's housing crisis. Dome software tour | geodesic dome tools | dome design suite | dome simulator | housing crisis toolchain",
"Fifty years from now, this skeleton still stands: code-generated video - discrepancies are probable - on geodesic dome construction as the future of housing. One frame, replaceable skins, zero bearing walls, and a build method that gets cheaper every time - promoting, advancing, developing, and mastering the dome as THE solution to America's housing crisis. Future of housing | geodesic dome future | durable dome home | housing innovation | dome construction tomorrow"
]

current := 1
if FileExist(stateFile) {
    try {
        saved := Integer(FileRead(stateFile))
        if (saved >= 1 and saved <= descriptions.Length)
            current := saved
    }
}

SaveState() {
    global stateFile, current
    handle := FileOpen(stateFile, "w")
    handle.Write(String(current))
    handle.Close()
}

SaveTabs() {
    global tabsFile, tabCount
    handle := FileOpen(tabsFile, "w")
    handle.Write(String(tabCount))
    handle.Close()
}

AdjustTabs(delta) {
    global tabCount
    tabCount += delta
    if (tabCount < 0)
        tabCount := 0
    if (tabCount > 40)
        tabCount := 40
    SaveTabs()
    ToolTip("Tabs between description fields: " tabCount
        . "  (F7 down, F8 up - next fields use this)", , , 20)
    SetTimer(() => ToolTip(), -3000)
}

TestTabs() {
    global tabCount
    if (tabCount > 0)
        Send("{Tab " tabCount "}")
    ToolTip("Sent Tab x" tabCount " with NO paste - check where focus landed."
        . " F7/F8 adjust, Ctrl+F7 to test again.", , , 20)
    SetTimer(() => ToolTip(), -4000)
}

; --- F9: the full batch ------------------------------------------------------

RunBatch() {
    global descriptions, batchStop, tabCount, PASTE_SETTLE, FIELD_SETTLE
    box := InputBox("How many videos to fill? Enter 1-" descriptions.Length
        . " (leave empty and press OK for all " descriptions.Length ").",
        "Batch paste")
    if (box.Result != "OK")
        return
    count := descriptions.Length
    if (box.Value != "") {
        try count := Integer(box.Value)
        catch
            count := descriptions.Length
    }
    if (count < 1)
        count := 1
    if (count > descriptions.Length)
        count := descriptions.Length
    tabsBox := InputBox("How many TAB presses does it take to reach the NEXT"
        . " video's description field? (currently " tabCount "; leave empty to"
        . " keep it. F7/F8 adjust it live during the batch.)",
        "Tab count")
    if (tabsBox.Result != "OK")
        return
    if (tabsBox.Value != "") {
        try tabCount := Integer(tabsBox.Value)
        catch
            tabCount := 4
    }
    if (tabCount < 0)
        tabCount := 0
    if (tabCount > 40)
        tabCount := 40
    SaveTabs()
    if (MsgBox("About to fill " count " description field(s) automatically."
        . "`n`nFocus the FIRST video's description field, then each cycle is:"
        . " Ctrl+A, paste, Tab x" tabCount ", Ctrl+A."
        . "`n`nContinue?", "Batch paste " count " descriptions", "YesNo") != "Yes")
        return
    batchStop := false
    for index, text in descriptions {
        if (index > count)
            break
        if batchStop {
            ToolTip("Batch stopped after " (index - 1) " of " count
                . " fields. Manual index is at " (index - 1) ".", , , 20)
            SetTimer(() => ToolTip(), -4000)
            return
        }
        Send("^a")                      ; select whatever is in the field
        Sleep 60
        A_Clipboard := FinalText(text)  ; load this video's description + 5 random hashtags
        ClipWait(1, 1)
        Sleep 80
        Send("^v")                      ; paste it
        Sleep PASTE_SETTLE
        if (index < count) {
            if (tabCount > 0)
                Send("{Tab " tabCount "}")   ; hop to the next description field
            Sleep FIELD_SETTLE
            Send("^a")                  ; select its current content, ready for next paste
            Sleep 60
        }
        ToolTip("Batch: " index "/" count "  (tabs: " tabCount ", F7/F8 adjust)", , , 20)
    }
    ToolTip("Batch complete - " count " description(s) pasted")
    SetTimer(() => ToolTip(), -4000)
}

; --- Ctrl+F9: paste one generic description by hand --------------------------

PasteGenericNext() {
    global descriptions, current
    A_Clipboard := FinalText(descriptions[current])
    ClipWait(1, 1)
    Sleep 80
    Send("^v")
    justPasted := current
    current := (current = descriptions.Length) ? 1 : current + 1
    SaveState()
    ToolTip("Pasted generic #" justPasted " of " descriptions.Length
        . ". Next: #" current, , , 20)
    SetTimer(() => ToolTip(), -3000)
}

; --- helpers ------------------------------------------------------------------

StopBatch() {
    global batchStop
    batchStop := true
    ToolTip("Stop requested - the batch halts after the current field")
    SetTimer(() => ToolTip(), -3000)
}

StepBack() {
    global descriptions, current
    if (current > 1)
        current -= 1
    SaveState()
    ToolTip("Manual index back to #" current " of " descriptions.Length
        . " - " SubStr(descriptions[current], 1, 90) "...", , , 20)
    SetTimer(() => ToolTip(), -3000)
}

ShowCurrent() {
    global descriptions, current
    ToolTip("Manual index: #" current " of " descriptions.Length
        . "`n" SubStr(descriptions[current], 1, 140) "...", , , 20)
    SetTimer(() => ToolTip(), -4000)
}

ResetIndex() {
    global current, descriptions
    current := 1
    SaveState()
    ToolTip("Reset manual index to #1 of " descriptions.Length)
    SetTimer(() => ToolTip(), -2000)
}

DumpAll() {
    global descriptions
    lines := ""
    for index, text in descriptions
        lines .= index ". " FinalText(text) "`n`n"
    path := A_ScriptDir "\descriptions_dump.txt"
    FileOpen(path, "w").Write(lines)
    MsgBox("Wrote all " descriptions.Length " descriptions to:`n" path)
}

F9::RunBatch
F7::AdjustTabs(-1)
F8::AdjustTabs(1)
^F7::TestTabs
^F9::PasteGenericNext
^F12::StopBatch
F10::StepBack
F11::ShowCurrent
F12::ResetIndex
^F11::DumpAll
