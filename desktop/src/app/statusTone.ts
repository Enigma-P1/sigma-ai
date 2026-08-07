/** Maps domain statuses (gate / prescore / tool-rail) to the design
 * system's generic pill/verdict tones. Kept separate from the components
 * themselves so StatusPill/VerdictBanner stay domain-agnostic. */
import type { PillTone } from "../design/components";
import type { VerdictTone } from "../design/components";
import type { GateStatus, PrescoreStatus } from "../api/types";

export function toneForGateStatus(status: GateStatus): PillTone {
  switch (status) {
    case "CLEAR":
      return "pass";
    case "SOFT_BLOCK":
      return "flag";
    case "HARD_BLOCK":
      return "fail";
    case "NOT_YET_BUILT":
      return "neutral";
  }
}

export function verdictToneForGateStatus(status: GateStatus): VerdictTone {
  switch (status) {
    case "CLEAR":
      return "pass";
    case "SOFT_BLOCK":
      return "flag";
    case "HARD_BLOCK":
      return "fail";
    case "NOT_YET_BUILT":
      return "neutral";
  }
}

export function toneForPrescoreStatus(status: PrescoreStatus): PillTone {
  switch (status) {
    case "pass":
      return "pass";
    case "flag":
      return "flag";
    case "hard_flag":
      return "fail";
  }
}

export type ToolRailStatus = "done" | "available" | "not-yet" | "blocked";

export function labelForToolStatus(status: ToolRailStatus): string {
  switch (status) {
    case "done":
      return "Done";
    case "available":
      return "Available";
    case "not-yet":
      return "Not yet built";
    case "blocked":
      return "Blocked";
  }
}

export function toneForToolStatus(status: ToolRailStatus): PillTone {
  switch (status) {
    case "done":
      return "pass";
    case "available":
      return "accent";
    case "not-yet":
      return "neutral";
    case "blocked":
      return "fail";
  }
}
