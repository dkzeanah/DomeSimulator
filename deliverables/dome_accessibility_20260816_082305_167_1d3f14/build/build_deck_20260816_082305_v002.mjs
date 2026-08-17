import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const RUN_DIR = "C:\\Users\\Don\\Desktop\\DomeSim\\deliverables\\dome_accessibility_20260816_082305_167_1d3f14";
const ASSET_DIR = path.join(RUN_DIR, "assets");
const RENDER_DIR = path.join(RUN_DIR, "renders", "v002");
const OUTPUT_PPTX = path.join(
  RUN_DIR,
  "wheelchair_first_dome_living_20260816_082305_v002.pptx",
);

const W = 1280;
const H = 720;
const C = {
  white: "#FFFFFF",
  ink: "#0A0A0A",
  muted: "#5B6470",
  panel: "#F1F2F4",
  rule: "#B8BCC4",
  blue: "#3D8DFF",
  bluePale: "#D0EDFA",
  blueDeep: "#145D8A",
  teal: "#1F7A7A",
  warm: "#F5F0E8",
};
const FONT = "Arial";

const imagePrompts = {
  hero: `Use case: photorealistic-natural. Asset type: persuasive presentation hero image for a wheelchair-accessible dome home. Show a dignified older adult wheelchair user independently approaching and entering a purpose-built, single-level geodesic dome through a flush, wide doorway from a broad straight gently sloped route with a level landing. Premium architectural editorial photography; warm natural materials; no text or watermark.`,
  circulation: `Use case: photorealistic-natural. Show an older adult wheelchair user moving independently from the entrance into a broad open-plan living and dining area inside a single-level geodesic dome. Continuous matte floor, wide route, straight radial partitions, uncluttered furniture, realistic architectural photography, no text.`,
  kitchen: `Use case: photorealistic-natural. Show an elderly wheelchair user preparing tea independently at a lowered pull-under work surface in an open kitchen inside a geodesic dome. Reachable storage and controls, broad turning area, residential rather than institutional, no text.`,
  bath: `Use case: photorealistic-natural. Show an older wheelchair user moving through a wide sliding doorway from a bedroom into an accessible bathroom in a geodesic dome. Flush floor, roll-in shower, fold-down seat, grab bars, wall-mounted sink, broad turning space, no text.`,
  cutaway: `Use case: stylized-concept. Create a polished isometric architectural cutaway of a single-level accessible geodesic dome home with a wheelchair user entering and a subtle blue floor path connecting the living area, kitchen, bedroom, and bathroom around an open central turning zone. No text.`,
};

async function assertAbsent(filePath) {
  try {
    await fs.access(filePath);
    throw new Error(`Refusing to overwrite existing artifact: ${filePath}`);
  } catch (error) {
    if (error?.code !== "ENOENT") throw error;
  }
}

async function readImage(name) {
  const bytes = await fs.readFile(path.join(ASSET_DIR, name));
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

async function writeBlobUnique(filePath, blob) {
  await assertAbsent(filePath);
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()), {
    flag: "wx",
  });
}

async function writeTextUnique(filePath, content) {
  await assertAbsent(filePath);
  await fs.writeFile(filePath, content, { encoding: "utf8", flag: "wx" });
}

function addShape(slide, position, fill, geometry = "rect", line = null, name = undefined) {
  return slide.shapes.add({
    geometry,
    name,
    position,
    fill,
    line: line ?? { style: "solid", fill: "none", width: 0 },
  });
}

function addText(slide, text, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position,
    fill: options.fill ?? "none",
    line: options.line ?? { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: options.fontSize ?? 24,
    typeface: options.typeface ?? FONT,
    color: options.color ?? C.ink,
    bold: options.bold ?? false,
    alignment: options.alignment ?? "left",
    verticalAlignment: options.verticalAlignment ?? "top",
    autoFit: options.autoFit ?? "none",
    wrap: options.wrap ?? "square",
    insets: options.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function addRichText(slide, paragraphs, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position,
    fill: options.fill ?? "none",
    line: options.line ?? { style: "solid", fill: "none", width: 0 },
  });
  shape.text.set(paragraphs);
  shape.text.style = {
    fontSize: options.fontSize ?? 24,
    typeface: options.typeface ?? FONT,
    color: options.color ?? C.ink,
    alignment: options.alignment ?? "left",
    verticalAlignment: options.verticalAlignment ?? "top",
    autoFit: options.autoFit ?? "none",
    wrap: "square",
    insets: options.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function bullet(lead, body, color = C.ink) {
  return {
    bulletCharacter: "•",
    marginLeft: 26,
    indent: -14,
    spaceAfter: 900,
    runs: [
      { run: lead, textStyle: { bold: true, color } },
      { run: body, textStyle: { color } },
    ],
  };
}

function header(slide, title, number, eyebrow = "WHEELCHAIR-FIRST DOME LIVING") {
  addText(slide, eyebrow, { left: 42, top: 30, width: 460, height: 24 }, {
    fontSize: 14,
    bold: true,
    color: C.blueDeep,
  });
  addText(slide, title, { left: 42, top: 70, width: 1160, height: 74 }, {
    fontSize: 47,
    bold: true,
    color: C.ink,
    autoFit: "shrinkText",
  });
  addShape(slide, { left: 42, top: 158, width: 1196, height: 1 }, C.rule, "rect", null, `top-rule-${number}`);
  addText(slide, String(number).padStart(2, "0"), { left: 1187, top: 672, width: 52, height: 20 }, {
    fontSize: 14,
    color: C.muted,
    alignment: "right",
  });
}

function repaintHeader(slide, title, number, eyebrow = "WHEELCHAIR-FIRST DOME LIVING") {
  addShape(slide, { left: 0, top: 0, width: W, height: 174 }, C.white, "rect");
  addText(slide, eyebrow, { left: 42, top: 30, width: 460, height: 24 }, {
    fontSize: 14,
    bold: true,
    color: C.blueDeep,
  });
  addText(slide, title, { left: 42, top: 70, width: 1160, height: 74 }, {
    fontSize: 47,
    bold: true,
    color: C.ink,
    autoFit: "shrinkText",
  });
  addShape(slide, { left: 42, top: 158, width: 1196, height: 1 }, C.rule, "rect", null, `repainted-top-rule-${number}`);
}

function addImage(slide, blob, alt, position, prompt, options = {}) {
  if (options.backing) {
    addShape(slide, {
      left: position.left - 10,
      top: position.top - 10,
      width: position.width + 20,
      height: position.height + 20,
    }, options.backing, "roundRect", { style: "solid", fill: C.rule, width: 1 });
  }
  return slide.images.add({
    blob,
    contentType: "image/png",
    alt,
    prompt,
    fit: options.fit ?? "cover",
    crop: options.crop,
    geometry: options.geometry ?? "roundRect",
    borderRadius: options.borderRadius ?? 14,
    position,
  });
}

function setNotes(slide, narration, sources = []) {
  const sourceLines = sources.length
    ? sources.map((source) => `- ${source}`).join("\n")
    : "- No external factual claim on this slide. Visuals are original AI-generated assets created for this deck.";
  slide.speakerNotes.textFrame.setText(
    `Narration\n${narration}\n\n[Sources]\n${sourceLines}\n[/Sources]`,
  );
  slide.speakerNotes.setVisible(true);
}

function baseSlide(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  return slide;
}

async function main() {
  await assertAbsent(OUTPUT_PPTX);
  await assertAbsent(RENDER_DIR);
  await fs.mkdir(RENDER_DIR, { recursive: false });

  const assets = {
    hero: await readImage("01_hero_entry.png"),
    circulation: await readImage("02_open_circulation.png"),
    kitchen: await readImage("03_accessible_kitchen.png"),
    bath: await readImage("04_bed_bath_suite.png"),
    cutaway: await readImage("05_dome_cutaway.png"),
  };

  const presentation = Presentation.create({ slideSize: { width: W, height: H } });

  // 1 — cover, based on the Codex Grid half-text/half-image hierarchy.
  {
    const slide = baseSlide(presentation);
    addText(slide, "WHEELCHAIR-FIRST DOME LIVING", { left: 42, top: 36, width: 470, height: 28 }, {
      fontSize: 15,
      bold: true,
      color: C.blueDeep,
    });
    addText(slide, "A home that\nmoves with you", { left: 42, top: 118, width: 544, height: 190 }, {
      fontSize: 72,
      bold: true,
      color: C.ink,
    });
    addText(slide, "Why a purpose-built, single-level dome can turn accessibility from an add-on into the organizing idea.", { left: 42, top: 346, width: 500, height: 132 }, {
      fontSize: 28,
      color: C.muted,
    });
    addShape(slide, { left: 42, top: 520, width: 150, height: 6 }, C.blue, "rect");
    addText(slide, "For wheelchair users, older adults, and anyone whose movement changes over time", { left: 42, top: 548, width: 530, height: 66 }, {
      fontSize: 22,
      color: C.blueDeep,
      bold: true,
    });
    addImage(
      slide,
      assets.hero,
      "Older wheelchair user independently approaching a flush, wide entrance to a modern geodesic dome home",
      { left: 635, top: 42, width: 603, height: 588 },
      imagePrompts.hero,
      { backing: C.bluePale, crop: { left: 0.08, top: 0, right: 0, bottom: 0 } },
    );
    addText(slide, "ACCESSIBLE HOUSING CONCEPT • 2026", { left: 42, top: 668, width: 450, height: 18 }, {
      fontSize: 13,
      color: C.muted,
    });
    setNotes(
      slide,
      "The strongest accessible home is not a conventional plan with a ramp added later. It begins with the person, the chair, and the path. A single-level dome can make that path the center of the architecture—if every threshold, turn, and reach is designed honestly.",
      ["Visual: original AI-generated image created for this deck with OpenAI ImageGen; prompt retained in the presentation metadata and companion manifest."],
    );
  }

  // 2 — image-led case for one level.
  {
    const slide = baseSlide(presentation);
    header(slide, "One level changes the whole day", 2);
    addImage(
      slide,
      assets.circulation,
      "Older wheelchair user crossing a flush entrance into a bright open-plan dome interior",
      { left: 42, top: 191, width: 706, height: 431 },
      imagePrompts.circulation,
      { crop: { left: 0, top: 0, right: 0.03, bottom: 0 } },
    );
    addText(slide, "The daily win", { left: 800, top: 205, width: 370, height: 38 }, {
      fontSize: 25,
      bold: true,
      color: C.blueDeep,
    });
    addRichText(slide, [
      bullet("No stairs or lift dependency. ", "The primary life of the house happens on one continuous floor."),
      bullet("No corridor maze. ", "Rooms open from a legible central space instead of a chain of tight turns."),
      bullet("No special route. ", "The accessible path is the same welcoming path everyone uses."),
    ], { left: 800, top: 266, width: 412, height: 310 }, { fontSize: 25 });
    addText(slide, "Accessibility becomes invisible—in the best possible way.", { left: 800, top: 574, width: 410, height: 60 }, {
      fontSize: 22,
      bold: true,
      color: C.teal,
    });
    setNotes(
      slide,
      "Independence is usually lost in small moments: one step at the entrance, one tight turn at the bedroom, one threshold at the shower. Put daily life on one continuous floor and those moments stop demanding help. The accessible route becomes simply the route.",
      [
        "National Institute on Aging, “Aging in Place: Growing Older at Home”: https://www.nia.nih.gov/health/aging-place-growing-older-home",
        "Visual: original AI-generated image created for this deck with OpenAI ImageGen.",
      ],
    );
  }

  // 3 — movement map and radial planning.
  {
    const slide = baseSlide(presentation);
    header(slide, "Start with a turning circle, then place the rooms", 3);
    addText(slide, "The dome works best when the open center becomes a mobility commons—not leftover space.", { left: 42, top: 194, width: 390, height: 100 }, {
      fontSize: 28,
      color: C.muted,
    });
    const steps = [
      ["01", "ENTER", "A flush doorway lands directly in the shared center."],
      ["02", "TURN", "Generous clear floor space absorbs direction changes."],
      ["03", "REACH", "Short radial routes connect kitchen, bed, and bath."],
    ];
    steps.forEach(([n, label, body], index) => {
      const top = 322 + index * 100;
      addText(slide, n, { left: 42, top, width: 54, height: 42 }, { fontSize: 20, bold: true, color: C.blue });
      addText(slide, label, { left: 112, top, width: 120, height: 36 }, { fontSize: 25, bold: true, color: C.ink });
      addText(slide, body, { left: 235, top, width: 215, height: 72 }, { fontSize: 22, color: C.muted, autoFit: "shrinkText" });
    });
    addImage(
      slide,
      assets.cutaway,
      "Isometric cutaway of a single-level accessible dome home with a blue movement path from the entry to living, kitchen, bedroom, and bathroom",
      { left: 488, top: 188, width: 750, height: 444 },
      imagePrompts.cutaway,
      { fit: "contain", backing: C.warm },
    );
    setNotes(
      slide,
      "A good accessible floor plan is a movement map. Enter without a level change. Turn without reversing through a narrow hall. Reach the kitchen, bedroom, and bathroom on short, obvious routes. The dome earns its value when its central volume is reserved for that movement.",
      [
        "ADA 2010 Standards, Sections 304–305, used here as best-practice dimensional references: https://www.ada.gov/law-and-regs/design-standards/2010-stds/",
        "Visual: original AI-generated image created for this deck with OpenAI ImageGen; conceptual, not a construction drawing.",
      ],
    );
  }

  // 4 — daily barriers, sparse four-point composition.
  {
    const slide = baseSlide(presentation);
    header(slide, "Every extra barrier becomes a daily tax", 4);
    addText(slide, "A plan can look generous on paper and still demand dozens of avoidable maneuvers every day.", { left: 42, top: 192, width: 1050, height: 48 }, {
      fontSize: 26,
      color: C.muted,
    });
    const taxes = [
      ["THRESHOLD", "A wheel catches. Momentum stops."],
      ["TURN", "A sharp corner forces backing and correction."],
      ["REACH", "A control sits beyond safe range."],
      ["TRANSFER", "A tight fixture turns privacy into assistance."],
    ];
    taxes.forEach(([word, body], index) => {
      const left = 42 + index * 300;
      addText(slide, `0${index + 1}`, { left, top: 310, width: 54, height: 34 }, { fontSize: 17, bold: true, color: C.blue });
      addShape(slide, { left, top: 363, width: 250, height: 2 }, index === 0 ? C.blue : C.rule, "rect");
      addText(slide, word, { left, top: 390, width: 260, height: 52 }, { fontSize: 29, bold: true, color: C.ink });
      addText(slide, body, { left, top: 468, width: 245, height: 94 }, { fontSize: 22, color: C.muted });
    });
    addText(slide, "The persuasive case for the dome is simple: spend the floor area on movement before spending it on walls.", { left: 42, top: 610, width: 1050, height: 45 }, {
      fontSize: 25,
      bold: true,
      color: C.blueDeep,
    });
    repaintHeader(slide, "Every extra barrier becomes a daily tax", 4);
    setNotes(
      slide,
      "Accessibility is cumulative. A threshold, a tight turn, a long reach, and a crowded transfer zone may each seem minor. Repeated across a day, they drain time, strength, and privacy. The plan should remove those taxes before the first wall is built.",
    );
  }

  // 5 — why the dome form helps.
  {
    const slide = baseSlide(presentation);
    header(slide, "The shell can organize space around movement", 5);
    addText(slide, "The dome is valuable here not because it is round, but because it can hold a broad central volume with fewer interior structural interruptions.", { left: 42, top: 194, width: 1140, height: 74 }, {
      fontSize: 27,
      color: C.muted,
    });
    const concepts = [
      ["CENTER", "Reserve it for turning, passing, gathering, and changing direction."],
      ["EDGE", "Place storage, utilities, and built-ins where movement does not need to be."],
      ["ROUTES", "Use short, straight radial connections—never a curved ramp as a design gesture."],
    ];
    concepts.forEach(([head, body], index) => {
      const left = 42 + index * 400;
      addText(slide, head, { left, top: 346, width: 335, height: 52 }, {
        fontSize: 34,
        bold: true,
        color: index === 1 ? C.teal : C.ink,
      });
      addShape(slide, { left, top: 420, width: 338, height: 1 }, C.rule, "rect");
      addText(slide, body, { left, top: 454, width: 338, height: 126 }, { fontSize: 23, color: C.muted });
    });
    addText(slide, "Curve the envelope. Keep the accessible route level, direct, and predictable.", { left: 42, top: 618, width: 950, height: 44 }, {
      fontSize: 27,
      bold: true,
      color: C.blueDeep,
    });
    setNotes(
      slide,
      "The dome’s structural shell can free the interior from the bearing walls that often chop a plan into corridors. But the curved exterior does not excuse curved circulation. Put the turning zone in the center, service functions at the edge, and connect rooms with short, level, straight routes.",
      ["ADA 2010 Standards, Advisory 405.7, cautions that tight curvilinear ramps can create compound cross slopes: https://www.ada.gov/law-and-regs/design-standards/2010-stds/"],
    );
  }

  // 6 — entry benchmarks.
  {
    const slide = baseSlide(presentation);
    header(slide, "The entrance is the first independence test", 6);
    addText(slide, "A beautiful house that requires help at the door is not accessible.", { left: 42, top: 194, width: 780, height: 50 }, {
      fontSize: 28,
      color: C.muted,
    });
    addText(slide, "32 in", { left: 42, top: 300, width: 290, height: 92 }, { fontSize: 72, bold: true, color: C.blue });
    addText(slide, "minimum clear door opening", { left: 42, top: 398, width: 300, height: 50 }, { fontSize: 23, bold: true });
    addText(slide, "Benchmark from the ADA Standards; local residential requirements and individual needs may differ.", { left: 42, top: 464, width: 320, height: 104 }, { fontSize: 22, color: C.muted, autoFit: "shrinkText" });
    addShape(slide, { left: 390, top: 280, width: 1, height: 304 }, C.rule, "rect");
    addRichText(slide, [
      bullet("Flush threshold. ", "Eliminate the small lip that stops casters and creates a trip edge."),
      bullet("Level landing. ", "Give the user room to stop, reach hardware, and operate the door."),
      bullet("Straight, gentle approach. ", "Use the least slope practical; if it is a ramp, design to the applicable standard."),
      bullet("Simple hardware. ", "Lever handles, low force, and powered opening where appropriate."),
    ], { left: 454, top: 292, width: 710, height: 300 }, { fontSize: 25 });
    addText(slide, "A shared, dignified front door—not a side-door accommodation.", { left: 454, top: 610, width: 720, height: 42 }, { fontSize: 26, bold: true, color: C.teal });
    setNotes(
      slide,
      "The entrance should pass four tests: a flush threshold, enough clear opening, enough landing space to operate the door, and the gentlest practical approach. The 32-inch number is a useful design benchmark, but the principle matters more: the front door must work independently.",
      ["ADA 2010 Standards, Sections 404.2.3 and 405: https://www.ada.gov/law-and-regs/design-standards/2010-stds/"],
    );
  }

  // 7 — kitchen.
  {
    const slide = baseSlide(presentation);
    header(slide, "The kitchen stays part of life", 7);
    addImage(
      slide,
      assets.kitchen,
      "Older wheelchair user preparing tea at a pull-under counter in an open kitchen inside a dome home",
      { left: 42, top: 190, width: 730, height: 438 },
      imagePrompts.kitchen,
      { crop: { left: 0.03, top: 0, right: 0.02, bottom: 0 } },
    );
    addText(slide, "Design for reach, not adaptation", { left: 820, top: 202, width: 390, height: 70 }, {
      fontSize: 32,
      bold: true,
      color: C.ink,
    });
    addRichText(slide, [
      bullet("Pull under. ", "Provide knee and toe clearance at a true work surface."),
      bullet("Bring storage down. ", "Use drawers, pull-outs, and reachable pantry zones."),
      bullet("Open the turning area. ", "Keep the chair clear of appliance doors and traffic."),
      bullet("Share the room. ", "An open kitchen keeps cooking social, visible, and connected."),
    ], { left: 820, top: 300, width: 390, height: 300 }, { fontSize: 22 });
    repaintHeader(slide, "The kitchen stays part of life", 7);
    setNotes(
      slide,
      "The kitchen is where accessible design becomes quality of life. Knee clearance, reachable storage, side-opening appliances, and room to turn keep a wheelchair user participating instead of watching. The dome’s open center can give the kitchen generous circulation without isolating it.",
      [
        "ADA 2010 Standards, Sections 305–306, used as best-practice clear floor, knee, and toe clearance references: https://www.ada.gov/law-and-regs/design-standards/2010-stds/",
        "Visual: original AI-generated image created for this deck with OpenAI ImageGen; features are illustrative and require project-specific verification.",
      ],
    );
  }

  // 8 — bed and bath.
  {
    const slide = baseSlide(presentation);
    header(slide, "Privacy depends on space to move", 8);
    addText(slide, "The bedroom and bathroom should reduce transfers, not create new ones.", { left: 42, top: 196, width: 420, height: 86 }, {
      fontSize: 28,
      color: C.muted,
    });
    addRichText(slide, [
      bullet("Wide sliding opening. ", "Avoid a door swing that steals maneuvering room."),
      bullet("Roll-in shower. ", "Use a flush floor, seat, controls within reach, and correctly placed grab bars."),
      bullet("Clear side approach. ", "Leave transfer space beside the bed and fixtures."),
      bullet("Reinforced straight walls. ", "Give rails and cabinetry solid mounting surfaces inside the curved shell."),
    ], { left: 42, top: 324, width: 428, height: 294 }, { fontSize: 22 });
    addImage(
      slide,
      assets.bath,
      "Older wheelchair user moving from a bedroom through a wide sliding doorway into a roll-in shower bathroom inside a dome home",
      { left: 520, top: 190, width: 718, height: 438 },
      imagePrompts.bath,
      { crop: { left: 0.01, top: 0, right: 0.02, bottom: 0 } },
    );
    setNotes(
      slide,
      "Bathroom space protects more than safety; it protects privacy. A wide sliding opening, a zero-threshold shower, a reachable seat and controls, and clear transfer zones let more routines remain independent. Straight reinforced service walls solve the practical mounting problem inside a curved shell.",
      [
        "ADA 2010 Standards, Sections 603–610, used as best-practice bathroom fixture and transfer references: https://www.ada.gov/law-and-regs/design-standards/2010-stds/",
        "Visual: original AI-generated image created for this deck with OpenAI ImageGen; conceptual, not a code-compliance drawing.",
      ],
    );
  }

  // 9 — three benchmark metrics, Codex Grid metric-led composition.
  {
    const slide = baseSlide(presentation);
    header(slide, "Small dimensions produce enormous freedom", 9);
    addText(slide, "Use these as early design checks. They are not a substitute for local residential code, an architect, or the user’s own chair and reach.", { left: 42, top: 194, width: 1120, height: 70 }, {
      fontSize: 24,
      color: C.muted,
    });
    const metrics = [
      ["60 in", "TURNING SPACE", "A clear circular benchmark for changing direction."],
      ["32 in", "CLEAR OPENING", "Minimum benchmark through a doorway opened to 90 degrees."],
      ["1:12", "MAXIMUM RAMP SLOPE", "Where a ramp is required; gentler is better whenever practical."],
    ];
    metrics.forEach(([stat, label, body], index) => {
      const left = 42 + index * 400;
      addShape(slide, { left, top: 330, width: 355, height: 262 }, index === 1 ? C.bluePale : C.panel, "roundRect", null, `metric-${index + 1}`);
      addText(slide, stat, { left: left + 30, top: 360, width: 290, height: 86 }, { fontSize: 62, bold: true, color: index === 1 ? C.blueDeep : C.ink });
      addText(slide, label, { left: left + 30, top: 472, width: 294, height: 38 }, { fontSize: 24, bold: true, color: C.blueDeep, autoFit: "shrinkText" });
      addText(slide, body, { left: left + 30, top: 523, width: 292, height: 70 }, { fontSize: 22, color: C.muted, autoFit: "shrinkText" });
    });
    repaintHeader(slide, "Small dimensions produce enormous freedom", 9);
    setNotes(
      slide,
      "Three numbers catch many plan failures early: sixty inches for a circular turning space, thirty-two inches of clear doorway opening, and no steeper than one in twelve where a ramp is required. In a private home, treat them as disciplined starting benchmarks and verify every project locally.",
      ["ADA 2010 Standards, Sections 304.3.1, 404.2.3, and 405.2: https://www.ada.gov/law-and-regs/design-standards/2010-stds/"],
    );
  }

  // 10 — aging and fall stakes.
  {
    const slide = baseSlide(presentation);
    header(slide, "Wheelchair flow also protects aging bodies", 10);
    addText(slide, "Designing out level changes, cluttered routes, and forced transfers helps more people than wheelchair users alone.", { left: 42, top: 194, width: 1110, height: 68 }, {
      fontSize: 27,
      color: C.muted,
    });
    addText(slide, "1 in 4", { left: 42, top: 320, width: 310, height: 100 }, { fontSize: 76, bold: true, color: C.blue });
    addText(slide, "U.S. adults age 65+ report falling each year", { left: 42, top: 432, width: 315, height: 82 }, { fontSize: 23, bold: true });
    addShape(slide, { left: 402, top: 316, width: 1, height: 245 }, C.rule, "rect");
    addText(slide, "37%", { left: 454, top: 320, width: 250, height: 100 }, { fontSize: 76, bold: true, color: C.teal });
    addText(slide, "of people who fall report injury needing medical treatment or restricting activity", { left: 454, top: 432, width: 310, height: 100 }, { fontSize: 22, bold: true });
    addShape(slide, { left: 808, top: 316, width: 1, height: 245 }, C.rule, "rect");
    addText(slide, "ONE FLOOR", { left: 860, top: 335, width: 330, height: 58 }, { fontSize: 38, bold: true, color: C.ink });
    addText(slide, "A design goal that benefits wheelchair users, people with walkers, anyone with fatigue, and future caregivers.", { left: 860, top: 432, width: 330, height: 104 }, { fontSize: 22, color: C.muted });
    addText(slide, "Aging in place works best when the house can change before the person has to leave.", { left: 42, top: 610, width: 1080, height: 42 }, { fontSize: 26, bold: true, color: C.blueDeep });
    setNotes(
      slide,
      "Accessible circulation is not a niche feature. Falls are the leading cause of injury for older adults, and more than fourteen million older Americans report falling each year. A level, legible, uncluttered home cannot prevent every fall, but it can remove avoidable environmental demands and support aging in place.",
      [
        "CDC, Older Adult Falls Data: https://www.cdc.gov/falls/data-research/index.html",
        "National Institute on Aging, “Aging in Place: Growing Older at Home”: https://www.nia.nih.gov/health/aging-place-growing-older-home",
      ],
    );
  }

  // 11 — explicit conventional vs dome comparison.
  {
    const slide = baseSlide(presentation);
    header(slide, "A wheelchair-first dome spends space differently", 11);
    addText(slide, "TYPICAL CONVENTIONAL RETROFIT", { left: 42, top: 206, width: 510, height: 34 }, { fontSize: 22, bold: true, color: C.muted });
    addText(slide, "PURPOSE-BUILT ACCESSIBLE DOME", { left: 684, top: 206, width: 510, height: 34 }, { fontSize: 22, bold: true, color: C.blueDeep });
    addShape(slide, { left: 621, top: 198, width: 1, height: 420 }, C.rule, "rect");
    addRichText(slide, [
      bullet("Circulation is leftover. ", "Hallways and corners are inherited from the existing plan.", C.muted),
      bullet("Access is appended. ", "A ramp, widened door, or lift solves one barrier at a time.", C.muted),
      bullet("Doors consume maneuvering room. ", "Multiple swings compete in small spaces.", C.muted),
      bullet("Future change is expensive. ", "Structure, plumbing, and floor levels limit adaptation.", C.muted),
    ], { left: 42, top: 278, width: 510, height: 320 }, { fontSize: 23, color: C.muted });
    addRichText(slide, [
      bullet("Movement is the organizing grid. ", "The open center is reserved for turning and passing.", C.ink),
      bullet("Access is the front door. ", "The shared route is level, direct, and dignified.", C.ink),
      bullet("Short radial routes replace long halls. ", "Key rooms remain visually and physically close.", C.ink),
      bullet("Straight service walls make adaptation easier. ", "Cabinetry, rails, and utilities stay practical.", C.ink),
    ], { left: 684, top: 278, width: 510, height: 320 }, { fontSize: 23 });
    addText(slide, "The advantage is not novelty. It is fewer barriers per day.", { left: 684, top: 614, width: 510, height: 38 }, { fontSize: 25, bold: true, color: C.teal });
    repaintHeader(slide, "A wheelchair-first dome spends space differently", 11);
    setNotes(
      slide,
      "The comparison is not dome versus every conventional house. A well-designed rectangular house can be excellent. The argument is about design priorities: typical retrofits inherit barriers, while a purpose-built dome can reserve its central volume for movement from the beginning.",
      ["This slide is a qualitative design comparison, not a universal claim about all conventional or dome homes."],
    );
  }

  // 12 — honest close and action.
  {
    const slide = baseSlide(presentation);
    addText(slide, "THE HONEST STANDARD", { left: 42, top: 36, width: 390, height: 28 }, { fontSize: 15, bold: true, color: C.blueDeep });
    addText(slide, "A dome is perfect only when the details are", { left: 42, top: 108, width: 1120, height: 70 }, { fontSize: 50, bold: true, color: C.ink });
    addText(slide, "built around a real body.", { left: 42, top: 184, width: 900, height: 92 }, { fontSize: 67, bold: true, color: C.blue });
    addShape(slide, { left: 42, top: 300, width: 1196, height: 1 }, C.rule, "rect");
    addRichText(slide, [
      bullet("Curve the shell—not the wheelchair path. ", "Routes remain level, straight, and predictable."),
      bullet("Use straight interior service walls. ", "They simplify cabinetry, plumbing, reinforcement, and grab bars."),
      bullet("Keep every essential room on the main floor. ", "Lofts may exist, but daily life cannot depend on them."),
      bullet("Test the plan with the actual user. ", "Chair size, reach, transfer method, fatigue, vision, and caregiver needs vary."),
    ], { left: 42, top: 348, width: 760, height: 264 }, { fontSize: 23 });
    addShape(slide, { left: 850, top: 350, width: 345, height: 278 }, C.bluePale, "roundRect");
    addText(slide, "NEXT STEP", { left: 884, top: 382, width: 280, height: 32 }, { fontSize: 22, bold: true, color: C.blueDeep });
    addText(slide, "Map one real user’s day—entry, turn, reach, transfer—before pricing the shell.", { left: 884, top: 430, width: 268, height: 174 }, { fontSize: 24, bold: true, color: C.ink });
    addText(slide, "Build a home that preserves choice, privacy, and belonging as movement changes.", { left: 42, top: 642, width: 1030, height: 38 }, { fontSize: 27, bold: true, color: C.teal });
    addText(slide, "12", { left: 1187, top: 672, width: 52, height: 20 }, { fontSize: 14, color: C.muted, alignment: "right" });
    setNotes(
      slide,
      "The dome is not a shortcut around good accessibility practice. It is a promising shell for doing that practice well. Start with a real person’s movement map, protect the central turning space, put essential rooms on one floor, and verify every detail with the user and qualified local professionals.",
      [
        "ADA 2010 Standards are referenced as design benchmarks; applicability to private residential construction varies by project and jurisdiction: https://www.ada.gov/law-and-regs/design-standards/2010-stds/",
        "National Institute on Aging, aging-in-place guidance: https://www.nia.nih.gov/health/aging-place-growing-older-home",
      ],
    );
  }

  const inspection = await presentation.inspect({
    kind: "slide,textbox,shape,image,notes",
    maxChars: 24000,
  });
  await writeTextUnique(path.join(RENDER_DIR, "deck-inspection.ndjson"), inspection.ndjson);

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await writeBlobUnique(path.join(RENDER_DIR, `${stem}.png`), png);
    const layout = await slide.export({ format: "layout" });
    await writeTextUnique(path.join(RENDER_DIR, `${stem}.layout.json`), await layout.text());
  }

  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await writeBlobUnique(path.join(RENDER_DIR, "deck-montage.webp"), montage);

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(OUTPUT_PPTX);
  console.log(JSON.stringify({ outputPptx: OUTPUT_PPTX, renderDir: RENDER_DIR, slideCount: presentation.slides.items.length }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
