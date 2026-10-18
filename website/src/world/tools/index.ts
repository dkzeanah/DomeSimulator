// Each tool space's working interface, by space key. A space with an entry here shows its tool
// in the control panel; one without shows what is coming. Porting a desktop tool means adding
// its own module (its tables exported by scripts/, its arithmetic tested against the Python)
// and one line here -- nothing else in the world needs to change.

import { lazy, type ComponentType, type LazyExoticComponent, type RefObject } from "react";
import type { World } from "../engine";

export interface ToolProps { world: RefObject<World | null>; colour: string }

export const TOOLS: Record<string, LazyExoticComponent<ComponentType<ToolProps>>> = {
  "dome-creator": lazy(() => import("../CreatorPanel")),
  "assembly-line": lazy(() => import("../AssemblyPanel")),
  foundation: lazy(() => import("../FoundationPanel")),
  "wedge-method": lazy(() => import("../WedgePanel")),
  zome: lazy(() => import("../ZomePanel")),
  "panel-creator": lazy(() => import("../PanelCreatorPanel")),
  "cell-wall": lazy(() => import("../CellWallPanel")),
  masterclass: lazy(() => import("../MasterclassPanel")),
};
