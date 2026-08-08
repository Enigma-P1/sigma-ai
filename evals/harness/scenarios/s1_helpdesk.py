"""S-1 -- Harborview Mutual internal IT help desk, routine-ticket
resolution time (continuous / cycle time). Held-out scenario: PLAN §9's
`named_exit: null` case -- no deliberate trap, but every ordinary honesty
rule (measurement check before baseline, stability gates capability
language, declared confound rides the proof) still applies.

Artifacts are built FROM evals/scenarios/s1-helpdesk/spec.md's story and
frontmatter `ground_truth` (never invented) -- the numbers that come back
from the engine are the binding verdicts (spec.md's own "Engine
verification transcript (2026-08-08, engine 0.1.0)" is the reference this
driver must reproduce); narrative fields here are concise paraphrases of
the spec, not the spec's own prose, so a diff between this file and
spec.md is expected and fine.
"""

from __future__ import annotations

import statistics
from pathlib import Path

from ..lib.client import EngineClient
from ..lib.recorder import Recorder
from . import common

PROJECT_ID = "eval-s1-helpdesk"
DATA = common.SCENARIOS_DATA_ROOT / "s1-helpdesk" / "data"

USL = 8.0
CHARTER_REF = "s1-charter"


def run(recorder: Recorder, engine: EngineClient) -> None:
    common.reset_project(engine, PROJECT_ID, "S-1 Harborview help desk (held-out golden)", "2026-07-01T09:00:00Z")

    baseline_values = common.read_csv_column(DATA / "tickets-baseline.csv", "resolution_hours")
    after_values = common.read_csv_column(DATA / "tickets-after.csv", "resolution_hours")
    baseline_mean = statistics.fmean(baseline_values)  # 26.714... -- exact, never hand-transcribed

    # ---------------------------------------------------------------- Define
    picker = {
        "schema_version": 1, "artifact_id": "s1-picker", "tool_id": "T-01",
        "created_at": "2026-07-01T09:10:00Z", "updated_at": "2026-07-01T09:10:00Z",
        "notes": "Five intake criteria, all Yes; no single obvious fix (queue discipline, approvals, and channels all suspect) -- full DMAIC, not the PDCA quick path.",
        "scope_narrow": {"answer": True, "detail": "Routine (P3) help-desk tickets only -- password resets, software installs, access grants; P1/P2 incidents and project work are out of scope."},
        "measurable_outcome": {"answer": True, "detail": "Resolution time in business hours, open to confirmed resolution, against the 8-hour service-catalog promise."},
        "data_obtainable": {"answer": True, "detail": "The ticket system logs a timestamp at every stage; the July baseline extract already carries the element times a stopwatch study would re-collect."},
        "process_owner_engaged": {"answer": True, "detail": "Naomi Castillo, help desk lead, is named owner-in-waiting; IT manager Victor Braun sponsors after the Q2 employee survey named IT turnaround the top irritant."},
        "business_impact_plausible": {"answer": True, "detail": "Status-chase contacts, reopen rework, and late access grants put Q2 cost in the low five figures per quarter -- COPQ worksheet does the arithmetic."},
        "route": "full-DMAIC",
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-01", "T-01", picker)
    common.gate_check(recorder, PROJECT_ID, "intake_picker_present")
    common.gate_check(recorder, PROJECT_ID, "intake_picker_not_exit01")

    copq = {
        "schema_version": 1, "artifact_id": "s1-copq", "tool_id": "T-02",
        "created_at": "2026-07-01T10:00:00Z", "updated_at": "2026-07-01T10:00:00Z",
        "notes": "Q2 2026 ingredients per the charter's cost case; the engine computes each row amount and the total. Late access for 9 new hires (avg 2.6 business days) is counted but not priced -- named, not included as a row, since idle-capability dollars could not be defended.",
        "rows": [
            {"category": "custom", "custom_label": "Status-chase contacts (tech time)", "quantity": 146.3, "rate": 34.0,
             "period": "Q2 2026", "basis": "1,463 logged status-chase contacts, Q2 2026, averaging 6 minutes tech time each (146.3 tech-hours); loaded tech rate $34/hour", "is_estimate": False},
            {"category": "rework", "custom_label": None, "quantity": 81.4, "rate": 34.0,
             "period": "Q2 2026", "basis": "74 reopened tickets, Q2 2026, averaging 1.1 hours rework each (81.4 tech-hours); loaded tech rate $34/hour", "is_estimate": False},
        ],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-02", "T-02", copq)

    charter = {
        "schema_version": 1, "artifact_id": CHARTER_REF, "tool_id": "T-03",
        "created_at": "2026-07-01T11:00:00Z", "updated_at": "2026-07-01T11:00:00Z",
        "notes": "Problem statement is magnitude-only (no cause, no fix); risks include the fall onboarding surge and approval-policy pushback.",
        "problem_statement": {
            "what": "Routine (P3) help-desk tickets take far longer to resolve than the published service-catalog promise.",
            "where": "Harborview Mutual internal IT help desk (~380-person regional insurance office).",
            "when": "Ongoing through 2026; June 2026 spot-pull and the July 2026 baseline window both confirm it.",
            "magnitude": {"number": 26.71, "unit": "business hours average resolution time, routine (P3) tickets", "period": "July 2026 baseline window (n=127)"},
        },
        "goal": {
            "statement": "Cut mean routine-ticket resolution time to at most 8.0 business hours by 2026-10-31, without degrading the reopen-rate or tech-overtime guardrails.",
            "metric_name": "Mean resolution time, routine (P3) tickets", "baseline_value": 26.71, "target_value": 8.0,
            "unit": "business hours", "target_date": "2026-10-31",
            "consequential_metrics": ["Reopened tickets per 100", "Tech overtime hours per week"],
        },
        "scope": {"in_scope": "Routine (P3) tickets: password resets, software installs, access grants, open-to-confirmed-resolution.",
                   "out_scope": "P1/P2 incidents, project work, and any ticket outside the routine queue."},
        "team": [
            {"name": "Naomi Castillo", "role": "Help desk lead (process owner)"},
            {"name": "Ben Okafor", "role": "Tech"}, {"name": "Lena Fischer", "role": "Tech"}, {"name": "Marco Diaz", "role": "Tech"},
            {"name": "Victor Braun", "role": "IT manager (sponsor)"},
        ],
        "process_owner": {"name": "Naomi Castillo", "role": "Help desk lead -- runs the daily triage and dispatch"},
        "timeline": [
            {"name": "Define complete", "date": "2026-07-10"}, {"name": "Measure complete (baseline in hand)", "date": "2026-08-05"},
            {"name": "Analyze complete (causes verified)", "date": "2026-08-20"}, {"name": "Improve complete (fix proven)", "date": "2026-10-09"},
            {"name": "Control plan in place", "date": "2026-10-31"},
        ],
        "business_impact": {"amount": 30967, "unit": "dollars per year",
                              "basis": "COPQ calculator Q2 2026 total ($7,742) x 4 -- labeled projection, Q2 actuals x4 basis stated"},
        "risks": [
            {"risk": "Fall onboarding class of 14 new hires starts 2026-09-21, inside the after window, and can only push access-grant volume (and resolution times) up", "likelihood": "high", "impact": "medium",
             "mitigation": "Declare the confound before the window opens; read its direction on the proof honestly", "owner": "Naomi Castillo"},
            {"risk": "Approval-policy pushback on any pre-approved access matrix change", "likelihood": "medium", "impact": "medium",
             "mitigation": "Queue the access matrix as a second, later pilot rather than bundling it with the dispatch-rule change", "owner": "Victor Braun"},
        ],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-03", "T-03", charter)

    sipoc = {
        "schema_version": 1, "artifact_id": "s1-sipoc", "tool_id": "T-04",
        "created_at": "2026-07-02T09:00:00Z", "updated_at": "2026-07-02T09:00:00Z", "notes": "Boundaries match the charter scope.",
        "supplier_input_pairs": [
            {"supplier": "Requester (staff/manager)", "input": "Ticket request (password reset, software install, access grant)"},
            {"supplier": "Manager (access grants only)", "input": "Approval decision"},
            {"supplier": "Ticket system", "input": "Timestamps at every stage"},
        ],
        "process_steps": [
            {"step_number": 1, "description": "Requester opens a ticket"},
            {"step_number": 2, "description": "Ticket sits in the shared queue until morning triage"},
            {"step_number": 3, "description": "Dispatcher assigns the ticket to a tech"},
            {"step_number": 4, "description": "Tech requests manager approval (access grants only)"},
            {"step_number": 5, "description": "Tech performs the work"},
            {"step_number": 6, "description": "Requester confirms resolution (or auto-confirms at +2 business days)"},
        ],
        "output_customer_pairs": [
            {"output": "Resolved ticket, requester-confirmed", "customer": "Requester (staff/manager)"},
            {"output": "Resolution-time record", "customer": "IT manager (capacity and staffing decisions)"},
        ],
        "scope_start": "Requester opens a ticket", "scope_end": "Requester confirms resolution (or auto-confirm)",
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-04", "T-04", sipoc)

    voc_ctq = {
        "schema_version": 1, "artifact_id": "s1-voc-ctq", "tool_id": "T-05",
        "created_at": "2026-07-02T10:00:00Z", "updated_at": "2026-07-02T10:00:00Z",
        "notes": "Q2 employee survey plus walk-up complaints land on one CTQ.",
        "customers": [{"role": "Internal -- staff/manager filing a routine ticket", "is_internal": True}],
        "statements": [
            {"statement_id": "S1", "customer_role": "Internal -- staff/manager filing a routine ticket",
             "text": "I open a ticket and just walk to the desk anyway -- nothing happens otherwise.", "source": "survey", "source_detail": "Q2 2026 employee survey verbatim"},
            {"statement_id": "S2", "customer_role": "Internal -- staff/manager filing a routine ticket",
             "text": "New hires can't get their access for days; I end up emailing Naomi directly.", "source": "interview", "source_detail": "Manager walk-up complaint, June 2026"},
        ],
        "needs": [{"need_id": "N1", "statement_ids": ["S1", "S2"], "text": "Get a routine IT request resolved within the promised business day, without having to chase it personally."}],
        "ctqs": [{"ctq_id": "C1", "need_id": "N1", "measure": "Elapsed business hours from ticket open to confirmed resolution",
                    "direction": "lower_is_better", "target": "8.0 business hours (the service-catalog promise)",
                    "critical_vs_easy_check": "Customer-critical: both verbatims are about the total wait, not any one step; the ticket system already timestamps every stage, so this isn't chosen for measurement convenience."}],
        "primary_ctq_id": "C1",
        "charter_metric_link": "C1 is the charter's primary metric: mean resolution time in business hours, target 8.0 by 2026-10-31, lower is better -- turnaround-of-incident-tickets (P1/P2) is explicitly out of scope.",
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-05", "T-05", voc_ctq)

    common.gate_check(recorder, PROJECT_ID, "define_to_measure")

    # --------------------------------------------------------------- Measure
    baseline_ds = common.upload_dataset(recorder, engine, PROJECT_ID, "dataset.tickets_baseline",
                                          DATA / "tickets-baseline.csv", "2026-07-31T17:00:00Z", tool_ids=["T-11"])
    after_ds = common.upload_dataset(recorder, engine, PROJECT_ID, "dataset.tickets_after",
                                       DATA / "tickets-after.csv", "2026-10-09T17:00:00Z", tool_ids=["T-11"], do_preview=False)

    process_map = {
        "schema_version": 1, "artifact_id": "s1-process-map", "tool_id": "T-06",
        "created_at": "2026-07-15T09:00:00Z", "updated_at": "2026-07-15T09:00:00Z",
        "notes": "Stage means from the event-log decomposition: queue 16.5h + dispatch-to-first-action 2.8h + hands-on 1.9h + confirmation 2.6h = 23.8h (matches the non-access group mean 23.76h); access grants add ~7.4h manager-approval wait on top (matches the access group mean 31.12h).",
        "lanes": [
            {"lane_id": "requester", "name": "Requester", "owner": "N/A"},
            {"lane_id": "queue", "name": "Shared ticket queue", "owner": "Naomi Castillo"},
            {"lane_id": "dispatcher", "name": "Dispatcher (daily triage)", "owner": "Naomi Castillo"},
            {"lane_id": "approver", "name": "Approving manager (access grants only)", "owner": "N/A"},
            {"lane_id": "tech", "name": "Tech", "owner": "Ben Okafor / Lena Fischer / Marco Diaz"},
        ],
        "steps": [
            {"step_id": "s1", "lane_id": "queue", "name": "Ticket sits unassigned in triage queue", "order": 1,
             "step_type": "non_value_add", "time_minutes": 990.0, "defect_point": False, "strata": ["channel"],
             "reason": "Naomi triages once each morning; anything after ~9:30 waits until the next morning to be assigned at all",
             "wastes": [{"waste_id": "waiting", "note": "Median 16.5h sit -- the single largest block of the cycle"}]},
            {"step_id": "s2", "lane_id": "dispatcher", "name": "Ticket assigned, awaiting tech first action", "order": 2,
             "step_type": "non_value_add", "time_minutes": 168.0, "defect_point": False, "strata": [],
             "reason": "Gap between assignment and a tech actually starting work", "wastes": [{"waste_id": "waiting", "note": "2.8h mean"}]},
            {"step_id": "s3", "lane_id": "approver", "name": "Manager approval wait (access grants only)", "order": 3,
             "step_type": "non_value_add", "time_minutes": 444.0, "defect_point": True, "strata": ["request_type"],
             "reason": "Approval is requested only when a tech first touches the ticket -- access grants alone", "wastes": [{"waste_id": "waiting", "note": "7.4h mean on access grants; requested late in the cycle, not at ticket open"}]},
            {"step_id": "s4", "lane_id": "tech", "name": "Tech performs hands-on work", "order": 4,
             "step_type": "value_add", "time_minutes": 114.0, "defect_point": False, "strata": ["tech"],
             "reason": "The transformation the requester is waiting on", "wastes": []},
            {"step_id": "s5", "lane_id": "requester", "name": "Requester confirms resolution", "order": 5,
             "step_type": "enabling", "time_minutes": 156.0, "defect_point": False, "strata": [],
             "reason": "Confirmation reply, or auto-confirm at +2 business days", "wastes": [{"waste_id": "waiting", "note": "2.6h mean confirmation lag"}]},
        ],
        "connectors": [
            {"from_step": "s1", "to_step": "s2", "label": "morning triage batch"}, {"from_step": "s2", "to_step": "s3", "label": "access grants only"},
            {"from_step": "s3", "to_step": "s4", "label": None}, {"from_step": "s2", "to_step": "s4", "label": "non-access tickets"},
            {"from_step": "s4", "to_step": "s5", "label": None},
        ],
        "demand": {"available_time_minutes": 540, "demand_units": 6},
        "layout": {"s1": {"x": 60, "y": 40}, "s2": {"x": 240, "y": 40}, "s3": {"x": 420, "y": 180}, "s4": {"x": 600, "y": 40}, "s5": {"x": 780, "y": 40}},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-06", "T-06", process_map)

    delay_rows = common.read_csv_rows(DATA / "delay-tallies.csv")
    check_sheet_categories = [
        ("sat_unassigned", "Sat unassigned in triage queue > 4h"), ("mgr_approval", "Waiting on manager approval"),
        ("requester_reply", "Waiting on requester reply"), ("reassigned", "Reassigned between techs"), ("license_stock", "License/stock wait"),
    ]
    label_by_reason = {
        "sat unassigned in triage queue > 4h": "Sat unassigned in triage queue > 4h", "waiting on manager approval": "Waiting on manager approval",
        "waiting on requester reply": "Waiting on requester reply", "reassigned between techs": "Reassigned between techs", "license/stock wait": "License/stock wait",
    }
    check_sheet = {
        "schema_version": 1, "artifact_id": "s1-check-sheet", "tool_id": "T-08",
        "created_at": "2026-07-06T08:00:00Z", "updated_at": "2026-07-31T17:00:00Z",
        "notes": "One mark per baseline ticket that blew the 8.0-hour promise (all 127), tagged with the largest wait segment in its event log.",
        "categories": [{"category_id": cid, "label": label} for cid, label in check_sheet_categories],
        "strata_fields": [{"key": "date", "label": "Date"}],
        "entries": [
            {"entry_id": f"E{i+1:03d}", "category_id": next(cid for cid, label in check_sheet_categories if label == label_by_reason[row["primary_delay_reason"]]),
             "timestamp": f"{row['date']}T17:00:00", "strata": {"date": row["date"]}, "note": row["ticket_id"]}
            for i, row in enumerate(delay_rows)
        ],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-08", "T-08", check_sheet)
    recorder.call("T-08.to_dataset", "POST", f"/project/{PROJECT_ID}/check-sheet/{check_sheet['artifact_id']}/to-dataset",
                   {"created_at": "2026-07-31T17:05:00Z"}, tool_ids=["T-08"])
    pareto_categories = [label_by_reason[row["primary_delay_reason"]] for row in delay_rows]
    recorder.call("T-14.pareto.delay_reasons", "POST", "/stats/pareto", {"categories": pareto_categories}, tool_ids=["T-14"])

    collection_plan = {
        "schema_version": 1, "artifact_id": "s1-collection-plan", "tool_id": "T-11",
        "created_at": "2026-07-03T09:00:00Z", "updated_at": "2026-07-03T09:00:00Z",
        "notes": "Chosen precisely because techs batch-close tickets at day's end, so the tech's close-click would flatter the number.",
        "metric_name": "Elapsed business hours, ticket open to confirmed resolution", "charter_metric_id": "C1",
        "operational_definition": {
            "what_measured": "Elapsed business hours for one routine ticket, open to confirmed resolution",
            "how_instrument": "Ticket-system timestamps: created timestamp to requester-confirmation-reply timestamp (or auto-confirm at +2 business days)",
            "precision_unit": "Tenths of a business hour, business-hours calendar 8:00-17:00 Mon-Fri",
            "starts_when": "Ticket-created timestamp", "stops_when": "Requester's confirmation reply, or auto-confirm at +2 business days",
            "two_people_confirmed": True,
        },
        "data_type": "continuous",
        "stratification_factors": [
            {"name": "request_type", "values_expected": ["password_reset", "software_install", "access_grant"]},
            {"name": "channel", "values_expected": ["portal", "email"]}, {"name": "tech", "values_expected": ["B.O.", "L.F.", "M.D."]},
        ],
        "no_stratification_reason": "",
        "logistics": {"who_collects": "Naomi Castillo (help desk lead) owns the extract", "where_collected": "Ticket system event log",
                       "when_how_often": "Every 2nd routine ticket, all three techs, both channels, 20 consecutive business days",
                       "planned_n": 130, "sample_size_rationale": "Engine sample-size panel, mean calculator: planning SD 6.5 (June spot-pull), margin 1.25h at 95% confidence returns n=104; achieved n=127."},
        "bias_note": "Every-2nd-ticket sampling across all techs and both channels, 20 consecutive business days -- not a single easy morning.",
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-11", "T-11", collection_plan)
    recorder.call("T-11.sample_size", "POST", "/stats/sample-size",
                   {"calculator": "mean", "planning_sd": 6.5, "margin_of_error": 1.25, "confidence_level": 0.95}, tool_ids=["T-11"])

    msa_rows = common.read_csv_rows(DATA / "msa-repeats.csv")
    msa = {
        "schema_version": 1, "artifact_id": "s1-msa", "tool_id": "T-12",
        "created_at": "2026-08-01T09:00:00Z", "updated_at": "2026-08-01T09:00:00Z",
        "notes": "12 baseline tickets spanning the observed range, each re-extracted blind from the event log five days after the first pass, same person.",
        "data_type": "continuous", "operator": "Naomi Castillo",
        "gauge_name": "Ticket-system event log, re-extracted by hand", "gauge_increment": 0.1, "usl": USL, "lsl": None,
        "continuous_items": [
            {"item_id": row["ticket_id"], "readings": [float(row["first_extract_hours"]), float(row["second_extract_hours"])]}
            for row in msa_rows
        ],
        "attribute_items": [],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-12", "T-12", msa)

    common.gate_check(recorder, PROJECT_ID, "measure_capability_language_requires_msa_pass")

    recorder.call("T-13.baseline", "POST", "/stats/baseline",
                   {"project_id": PROJECT_ID, "dataset_id": baseline_ds["dataset_id"], "column": "resolution_hours",
                    "usl": USL, "lsl": None, "operational_definition_ok": True}, tool_ids=["T-13"])
    recorder.call("T-13.after_window", "POST", "/stats/baseline",
                   {"project_id": PROJECT_ID, "dataset_id": after_ds["dataset_id"], "column": "resolution_hours",
                    "usl": USL, "lsl": None, "operational_definition_ok": True}, tool_ids=["T-13"])
    recorder.call("T-14.descriptive.baseline", "POST", "/stats/descriptive", {"data": baseline_values}, tool_ids=["T-14"])

    common.gate_check(recorder, PROJECT_ID, "measure_to_analyze")

    # -------------------------------------------------------------- Analyze
    fishbone = {
        "schema_version": 1, "artifact_id": "s1-fishbone", "tool_id": "T-15",
        "created_at": "2026-08-06T09:00:00Z", "updated_at": "2026-08-07T09:00:00Z",
        "notes": "Verified causes carry evidence; investigating/candidate/ruled-out states used honestly per the spec's arc.",
        "effect": {"text": "Routine tickets average 26.71 business hours against the 8.0-hour promise (baseline n=127, stable, one-sided Cpk -0.96, 127/127 over the promise)", "charter_ref": CHARTER_REF},
        "causes": [
            {"cause_id": "c-triage-batch", "branch": "method", "text": "Once-a-day triage batch: anything arriving after ~9:30 waits until the next morning to be assigned at all",
             "parent_cause_id": None, "status": "verified", "evidence": {"kind": "check_sheet", "ref": "s1-check-sheet"}, "why_chain_position": None},
            {"cause_id": "c-scheduled-event", "branch": "method", "text": "Assignment is a scheduled event (Naomi's 8:30 triage block), not a continuous flow",
             "parent_cause_id": "c-triage-batch", "status": "verified",
             "evidence": {"kind": "observation_note", "ref": "Process map s1 (queue): 16.5h mean sit -- the dominant stage, engine-named readout"}, "why_chain_position": 1},
            {"cause_id": "c-approval-wait", "branch": "method", "text": "Manager approval on access grants is requested late (only when a tech first touches the ticket), adding ~7.4h",
             "parent_cause_id": None, "status": "verified", "evidence": {"kind": "check_sheet", "ref": "s1-check-sheet"}, "why_chain_position": None},
            {"cause_id": "c-email-lag", "branch": "method", "text": "Email-channel tickets show a small extra lag versus portal tickets",
             "parent_cause_id": None, "status": "investigating", "evidence": {"kind": "observation_note", "ref": "Collection-plan stratified view: email +2.4h vs portal in the plan's strata -- real but minor, not yet linked to the gap"}, "why_chain_position": None},
            {"cause_id": "c-tech-skill", "branch": "people", "text": "Tech skill mix may affect resolution speed", "parent_cause_id": None, "status": "candidate", "evidence": None, "why_chain_position": None},
            {"cause_id": "c-ticket-form", "branch": "method", "text": "Ticket-form quality (missing details) may force back-and-forth", "parent_cause_id": None, "status": "candidate", "evidence": None, "why_chain_position": None},
            {"cause_id": "c-extraction-error", "branch": "measurement", "text": "Event-log extraction / clock error could be inflating recorded waits",
             "parent_cause_id": None, "status": "ruled_out", "evidence": {"kind": "observation_note", "ref": "T-12 measurement check passed at 1.66% repeatability (s1-msa)"}, "why_chain_position": None},
            {"cause_id": "c-tech-capacity", "branch": "people", "text": "Techs are overloaded (capacity-constrained)", "parent_cause_id": None, "status": "ruled_out",
             "evidence": {"kind": "observation_note", "ref": "Hands-on work is only 1.9h of the 26.7h cycle (process map s4) -- techs are not idle and not the bottleneck"}, "why_chain_position": None},
        ],
        "layout": {},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-15", "T-15", fishbone)

    fmea = {
        "schema_version": 1, "artifact_id": "s1-fmea", "tool_id": "T-16",
        "created_at": "2026-08-06T14:00:00Z", "updated_at": "2026-08-07T10:00:00Z",
        "notes": "Process FMEA on the request flow. Highest-severity row is access-granted-with-wrong-scope (severity 8, security exposure) -- low RPN by frequency, surfaced by the severity-first view. Highest-RPN row is the mis-routed-then-forgotten ticket.",
        "rows": [
            {"row_id": "r-misrouted", "process_step_ref": "s2", "step_name": "Ticket assigned, awaiting tech first action",
             "failure_mode": "Ticket mis-routed to the wrong tech and sits unnoticed", "effect": "Resolution stalls well past the promise with nobody chasing it",
             "cause": "No cross-check between assignment and tech acknowledgment", "severity": 5, "occurrence": 7, "detection": 8,
             "action": "Add a 4-hour unacknowledged-assignment alert to the dispatcher view", "action_owner": "Naomi Castillo", "action_due": "2026-09-01", "action_status": "open", "anchors_consulted": True},
            {"row_id": "r-wrong-scope", "process_step_ref": "s3", "step_name": "Manager approval wait (access grants only)",
             "failure_mode": "Access granted with wrong scope (excess permissions)", "effect": "Security exposure -- an over-privileged account",
             "cause": "Approval request doesn't name the exact scope requested", "severity": 8, "occurrence": 2, "detection": 6,
             "action": "Approver checklist naming exact scope + quarterly access review", "action_owner": "Victor Braun", "action_due": "2026-09-15", "action_status": "open", "anchors_consulted": True},
            {"row_id": "r-wrong-approver", "process_step_ref": "s3", "step_name": "Manager approval wait (access grants only)",
             "failure_mode": "Approval request sent to the wrong or former manager", "effect": "Approval stalls until the requester notices and re-routes it",
             "cause": "Org-chart data in the ticket system goes stale", "severity": 6, "occurrence": 4, "detection": 5,
             "action": "Quarterly org-chart sync for the approval routing table", "action_owner": "Victor Braun", "action_due": "2026-09-30", "action_status": "open", "anchors_consulted": True},
            {"row_id": "r-premature-close", "process_step_ref": "s5", "step_name": "Requester confirms resolution",
             "failure_mode": "Ticket closed without a genuine confirmation, then reopens", "effect": "Requester's issue isn't actually fixed; a second cycle starts",
             "cause": "Auto-confirm at +2 business days treated as equivalent to a real confirmation", "severity": 4, "occurrence": 6, "detection": 5,
             "action": "Flag auto-confirmed tickets for a follow-up satisfaction check", "action_owner": "Naomi Castillo", "action_due": "2026-09-10", "action_status": "open", "anchors_consulted": True},
        ],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-16", "T-16", fmea)

    access_values = [float(r["resolution_hours"]) for r in common.read_csv_rows(DATA / "tickets-baseline.csv") if r["request_type"] == "access_grant"]
    rest_values = [float(r["resolution_hours"]) for r in common.read_csv_rows(DATA / "tickets-baseline.csv") if r["request_type"] != "access_grant"]
    hyp = {
        "schema_version": 1, "artifact_id": "s1-hyp-access", "tool_id": "T-17",
        "created_at": "2026-08-07T09:00:00Z", "updated_at": "2026-08-07T09:00:00Z",
        "notes": "The one pre-declared primary Analyze comparison: access grants vs other routine tickets, baseline window.",
        "declared_primary": True,
        "question": {
            "question_text": "Are access-grant tickets slower to resolve than other routine tickets (baseline window)?",
            "comparison_type": "two_independent", "declared_data_type": "continuous",
            "groups": [{"label": "access_grant", "values": access_values, "successes": None, "n": None},
                        {"label": "other_routine", "values": rest_values, "successes": None, "n": None}],
            "paired_before": None, "paired_after": None, "paired_before_label": "before", "paired_after_label": "after",
            "sample": None, "sample_label": "sample", "target": None, "contingency_table": None, "row_labels": None, "col_labels": None,
            "time_ordered": False, "user_shape_concern": False, "measurements_per_unit": 1, "question_intent": None,
            "comparisons_declared": 1, "tests_run_including_this_one": 1, "declared_primary": True,
        },
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-17", "T-17", hyp)

    common.gate_check(recorder, PROJECT_ID, "analyze_to_improve")

    # -------------------------------------------------------------- Improve
    solution_matrix = {
        "schema_version": 1, "artifact_id": "s1-solution-matrix", "tool_id": "T-18",
        "created_at": "2026-08-08T09:00:00Z", "updated_at": "2026-08-08T11:00:00Z",
        "notes": "Weights declared before scores. Dispatch rule ranks first (highest impact-per-effort on the #1 cause); access matrix second (queued, not rejected); the hire ranks last -- capacity was never the verified cause.",
        "solutions": [
            {"solution_id": "sol-dispatch-rule", "name": "Assign-on-arrival dispatch rule",
             "description": "Kill the once-a-day triage batch; each new routine ticket is assigned within the hour by a rotating dispatcher-of-the-day. $0, method change, attacks the #1 verified cause directly.",
             "linked_cause_ids": ["c-triage-batch", "c-scheduled-event"], "impact": 5, "effort": 2,
             "criterion_scores": [{"criterion_id": "crit-gap-impact", "score": 5, "scored_at": "2026-08-08T11:00:00Z"},
                                     {"criterion_id": "crit-effort", "score": 4, "scored_at": "2026-08-08T11:00:00Z"},
                                     {"criterion_id": "crit-cost", "score": 5, "scored_at": "2026-08-08T11:00:00Z"}]},
            {"solution_id": "sol-access-matrix", "name": "Pre-approved access matrix for standard roles",
             "description": "Policy change removing the manager-approval wait for standard, pre-defined role/access pairs. Needs Braun + department sign-offs before it can pilot.",
             "linked_cause_ids": ["c-approval-wait"], "impact": 4, "effort": 3,
             "criterion_scores": [{"criterion_id": "crit-gap-impact", "score": 3, "scored_at": "2026-08-08T11:00:00Z"},
                                     {"criterion_id": "crit-effort", "score": 2, "scored_at": "2026-08-08T11:00:00Z"},
                                     {"criterion_id": "crit-cost", "score": 4, "scored_at": "2026-08-08T11:00:00Z"}]},
            {"solution_id": "sol-hire-tech", "name": "Hire a fourth tech (~$68k/yr)",
             "description": "Capacity fix. Ranked as the honest loser: capacity was never the verified cause (hands-on work is only 1.9h of the 26.7h cycle).",
             "linked_cause_ids": ["c-tech-capacity"], "impact": 2, "effort": 1,
             "criterion_scores": [{"criterion_id": "crit-gap-impact", "score": 1, "scored_at": "2026-08-08T11:00:00Z"},
                                     {"criterion_id": "crit-effort", "score": 1, "scored_at": "2026-08-08T11:00:00Z"},
                                     {"criterion_id": "crit-cost", "score": 1, "scored_at": "2026-08-08T11:00:00Z"}]},
        ],
        "criteria": [
            {"criterion_id": "crit-gap-impact", "name": "Gap impact (5 = attacks the largest verified block)", "weight": 0.5, "declared_at": "2026-08-08T09:00:00Z"},
            {"criterion_id": "crit-effort", "name": "Effort/speed to implement (5 = startable within a week)", "weight": 0.25, "declared_at": "2026-08-08T09:00:00Z"},
            {"criterion_id": "crit-cost", "name": "Cost (5 = near-zero spend, 1 = major recurring cost)", "weight": 0.25, "declared_at": "2026-08-08T09:00:00Z"},
        ],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-18", "T-18", solution_matrix)

    pilot = {
        "schema_version": 1, "artifact_id": "s1-pilot", "tool_id": "T-19",
        "created_at": "2026-09-01T09:00:00Z", "updated_at": "2026-10-09T17:00:00Z",
        "notes": "One change only -- a draft bundling the access matrix into the same pilot was refused with EXIT-10, and the access matrix stayed queued for its own later pilot.",
        "the_one_change": {"statement": "Assign-on-arrival dispatch rule: kill the once-a-day triage batch; each new routine ticket is assigned within the hour by a rotating dispatcher-of-the-day.",
                             "linked_solution_id": "sol-dispatch-rule", "linked_cause_ids": ["c-triage-batch", "c-scheduled-event"]},
        "changes": [{"change_id": "chg-1", "text": "Assign-on-arrival dispatch rule: kill the once-a-day triage batch; each new routine ticket is assigned within the hour by a rotating dispatcher-of-the-day."}],
        "comparison_design": {"kind": "before_period", "description": "The frozen July baseline (tickets-baseline.csv, n=127, mean 26.71, stable) vs the measured after window."},
        "inclusion": {"who_or_what": "All routine (P3) tickets, all three techs, both channels, every 2nd ticket sampled -- the T-11 collection plan's rule",
                        "how_selected": "Same systematic every-2nd-ticket rule as the baseline",
                        "honesty_note": "Same desk, same techs as the baseline -- no randomization across sites."},
        "success_threshold": {"metric_ref": "resolution_hours (charter C1) -- after-window mean", "direction": "lower_is_better", "value": 12.0, "declared_at": "2026-09-03T09:00:00Z"},
        "analysis_plan": {"expected_route": "welch_two_sample_t", "rationale": "Two independent windows of continuous resolution hours -- Welch's t is the engine's two-independent-means default."},
        "falsification_line": "Two settled weeks above 12.0 business hours -> revert to batch triage and take the next-ranked cause.",
        "confounder_checklist": {
            "staffing": {"changed": False, "note": "Same three techs and dispatch lead throughout."},
            "season": {"changed": True, "note": "Fall onboarding class of 14 new hires starts 2026-09-21, inside the after window -- can only push access-grant volume (and resolution times) up, never manufacture a win."},
            "demand": {"changed": False, "note": "No other volume change beyond the onboarding class noted above."},
            "measurement": {"changed": False, "note": "Same operational definition and extraction procedure as the baseline; T-12 still stands."},
            "other": {"changed": False, "note": "No ticketing-system or approval-policy change landed in the window."},
        },
        "status": "complete",
    }
    bundled = dict(pilot)
    bundled["changes"] = [*pilot["changes"], {"change_id": "chg-2", "text": "Pre-approved access matrix for standard roles -- bundled in to save a second pilot round."}]
    common.validate_only(recorder, engine, "T-19", "T-19.exit10_probe", bundled, expect_status=(422,))
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-19", "T-19", pilot)

    proof = {
        "schema_version": 1, "artifact_id": "s1-proof", "tool_id": "T-20",
        "created_at": "2026-10-09T17:30:00Z", "updated_at": "2026-10-09T17:30:00Z",
        "notes": "Measured after window 2026-09-14 to 2026-10-09 (n=124); the 2026-09-07..09-11 bedding-in week excluded by declaration.",
        "pilot_ref": "s1-pilot", "metric_ref": "resolution_hours (charter C1: mean resolution time, routine tickets)",
        "operational_definition_ref": "s1-collection-plan", "measurement_system_ref": "s1-msa",
        "usl": USL, "lsl": None, "operational_definition_ok": True,
        "before": {"dataset_id": baseline_ds["dataset_id"], "dataset_sha256": baseline_ds["sha256"], "column": "resolution_hours", "values": baseline_values},
        "after": {"dataset_id": after_ds["dataset_id"], "dataset_sha256": after_ds["sha256"], "column": "resolution_hours", "values": after_values},
        "declared_threshold": {"metric_ref": "resolution_hours (charter C1) -- after-window mean", "direction": "lower_is_better", "value": 12.0, "declared_at": "2026-09-03T09:00:00Z"},
        "confounders": {
            "staffing": {"changed": False, "note": "Same three techs and dispatch lead throughout."},
            "season": {"changed": True, "note": "Fall onboarding class of 14 new hires started 2026-09-21, inside the measured window -- can only push access-grant volume up, never manufacture a win."},
            "demand": {"changed": False, "note": "No other volume change beyond the onboarding class."},
            "measurement": {"changed": False, "note": "Same operational definition and extraction procedure as the baseline."},
            "other": {"changed": False, "note": "No ticketing-system or approval-policy change landed in the window."},
        },
        "guardrails": [
            {"metric_ref": "reopened tickets per 100 (guardrail)", "direction": "lower_is_better", "before_value": 9.1, "after_value": 7.8},
            {"metric_ref": "tech overtime hours per week (guardrail)", "direction": "lower_is_better", "before_value": 3.5, "after_value": 3.1},
        ],
        "charter_ref": CHARTER_REF, "charter_baseline_value": baseline_mean, "charter_goal_value": USL, "charter_goal_direction": "lower_is_better",
        "next_cause_ref": {"cause_id": "c-approval-wait", "cause_text": "Manager approval on access grants is requested late, adding ~7.4h",
                             "via_solution_id": "sol-access-matrix", "via_solution_name": "Pre-approved access matrix for standard roles", "rank": 2},
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-20", "T-20", proof)

    common.gate_check(recorder, PROJECT_ID, "improve_to_control")

    # -------------------------------------------------------------- Control
    control_chart = common.prepare_control_chart({
        "schema_version": 1, "artifact_id": "s1-control-chart", "tool_id": "T-21",
        "created_at": "2026-10-09T18:00:00Z", "updated_at": "2026-10-09T18:00:00Z",
        "notes": "I-MR frozen from the measured after window (124 points, engine-verified signal-free before freezing). The catalog's 8.0h stays a drawn spec line, never a control limit.",
        "chart_type": "imr", "metric_ref": "resolution_hours (charter C1)",
        "selector": {"data_shape": "continuous", "defectives_or_defects": None},
        "source": {"kind": "dataset", "dataset_id": after_ds["dataset_id"], "dataset_sha256": after_ds["sha256"], "column": "resolution_hours"},
        "imr_values": after_values, "rule2_enabled": False, "rule3_enabled": False,
        "recalculation_log": [], "armed": {"monitoring_started": True, "cadence_note": "Naomi enters each week's sampled tickets; signals checked at entry against the frozen band."},
        "acknowledgments": {},
    }, action_at="2026-10-09T18:00:00Z")
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-21", "T-21", control_chart, strip=False)

    control_plan = common.prepare_control_plan({
        "schema_version": 1, "artifact_id": "s1-control-plan", "tool_id": "T-22",
        "created_at": "2026-10-09T18:30:00Z", "updated_at": "2026-10-12T09:00:00Z",
        "notes": "Monitors C1 weekly, the reopen guardrail, and the method itself (dispatch-within-the-hour compliance) so a lapsed method is caught before the chart has to catch it.",
        "monitored_items": [
            {"item_id": "mi-resolution", "characteristic": "Mean resolution time, routine tickets (charter C1, primary CTQ)",
             "how_measured": "Ticket-system timestamps, business hours, tenths -- the T-11 operational definition, unchanged", "operational_definition_ref": "s1-collection-plan",
             "where": "Ticket system event log", "frequency": "Weekly", "frequency_reason": "Matches the sampling cadence the limits were frozen from",
             "is_primary_ctq": True, "is_improve_change": False, "owner_name": "Naomi Castillo", "owner_accepted": True, "per_shift_owners": []},
            {"item_id": "mi-reopen", "characteristic": "Reopened tickets per 100 (guardrail)", "how_measured": "Reopen count / total closed tickets x100, weekly roll-up",
             "operational_definition_ref": "", "where": "Ticket system", "frequency": "Weekly", "frequency_reason": "Same cadence as the primary CTQ",
             "is_primary_ctq": False, "is_improve_change": False, "owner_name": "Naomi Castillo", "owner_accepted": True, "per_shift_owners": []},
            {"item_id": "mi-method", "characteristic": "Dispatch-within-the-hour compliance (the changed method itself)",
             "how_measured": "Spot-check: assignment timestamp minus ticket-created timestamp, sampled weekly", "operational_definition_ref": "",
             "where": "Ticket system", "frequency": "Weekly", "frequency_reason": "A lapsed method is the failure mode the chart cannot see directly",
             "is_primary_ctq": False, "is_improve_change": True, "owner_name": "Naomi Castillo", "owner_accepted": True, "per_shift_owners": []},
        ],
        "ocap_entries": [
            {"ocap_id": "ocap-resolution", "monitored_item_id": "mi-resolution",
             "trigger_signal": "Any point beyond the frozen band, or 8 consecutive points one side of center",
             "action_steps": ["First response: check dispatch-within-the-hour compliance for the signal week before anything else.",
                                 "Containment: if the queue is backing up, add a second dispatcher for the day; log the reason."],
             "escalation_trigger": "Two signals inside one rolling month", "escalation_contact": "Victor Braun (IT manager, sponsor)", "acting_owner": "Naomi Castillo"},
        ],
        "training_rows": [
            {"row_id": "tr-techs", "who": "Ben Okafor, Lena Fischer, Marco Diaz (techs)", "sop_ref": "s1-standard-work", "by_whom": "Naomi Castillo",
             "by_when": "2026-10-15", "verified_how": "Observed a full dispatcher-of-the-day rotation cycle", "verified_at": "2026-10-13", "done": True},
        ],
        "check_in_schedule": {
            "cadence": {"unit": "weeks", "interval": 1}, "start_date": "2026-10-16", "control_chart_ref": "s1-control-chart",
            "frozen_limits": {"control_chart_artifact_id": "s1-control-chart", "chart_type": "imr", "center": 7.2169, "ucl": 13.827, "lcl": 0.6069, "p_bar": None, "frozen_at": "2026-10-09T18:00:00Z"},
            "completed": [{"check_in_id": "ci-1", "label": "week 1: is the fix holding?", "due_date": "2026-10-16", "completed_at": "2026-10-16T17:00:00Z",
                             "entered": {"kind": "manual", "dataset_id": None, "values": [6.8, 7.5, 7.9, 6.2, 8.1, 7.0], "subgroup": None}, "note": "First week after freeze; no signals expected."}],
        },
        "as_of": "2026-10-16T17:00:00Z",
    })
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-22", "T-22", control_plan, strip=False)

    standard_work = {
        "schema_version": 1, "artifact_id": "s1-standard-work", "tool_id": "T-24",
        "created_at": "2026-10-09T19:00:00Z", "updated_at": "2026-10-09T19:00:00Z",
        "notes": "The dispatch rule as standard work.",
        "title": "Routine-ticket dispatch (assign-on-arrival)", "version": 1, "owner": "Naomi Castillo", "effective_date": "2026-09-07",
        "supersedes": "The once-a-day morning triage batch", "seeded_from_process_map_id": "s1-process-map", "linked_control_plan_id": "s1-control-plan",
        "steps": [
            {"step_id": "st-1", "order": 1, "action": "Watch the shared queue continuously (rotating dispatcher-of-the-day)",
             "standard": "No ticket sits unassigned more than one business hour", "changed_from_prior": True, "source_step_ref": "s1", "note": "Replaces the once-a-day 8:30 triage block"},
            {"step_id": "st-2", "order": 2, "action": "Assign the ticket to a tech within the hour",
             "standard": "Assignment timestamp - created timestamp <= 1 business hour", "changed_from_prior": True, "source_step_ref": "s2", "note": ""},
            {"step_id": "st-3", "order": 3, "action": "For access grants, fire the approval request at assignment, naming the exact scope requested",
             "standard": "Approval request sent the same hour as assignment, scope named", "changed_from_prior": True, "source_step_ref": "s3", "note": "FMEA action r-wrong-scope folded in"},
            {"step_id": "st-4", "order": 4, "action": "Perform the work and mark resolved", "standard": "Unchanged from prior practice", "changed_from_prior": False, "source_step_ref": "s4", "note": ""},
        ],
        "change_log": [{"version": 1, "at": "2026-10-09T19:00:00Z", "note": "v1 effective: dispatch-on-arrival written as the one standard method."}],
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-24", "T-24", standard_work)

    common.gate_check(recorder, PROJECT_ID, "control_to_wrap")

    # ----------------------------------------------------------------- Wrap
    a3 = {
        "schema_version": 1, "artifact_id": "s1-a3", "tool_id": "T-25",
        "created_at": "2026-10-20T09:00:00Z", "updated_at": "2026-10-20T09:00:00Z",
        "notes": "No claim upgraded in transit: the mean promise is kept (goal met, remaining -0.78), the every-ticket promise honestly is not.",
        "panels": [
            {"panel": "background", "seeded_from": {"artifact_ref": CHARTER_REF, "tool_id": "T-03", "fields": ["problem_statement", "business_impact"]},
             "narrative": "Routine tickets averaged 26.71 business hours against the 8-hour service-catalog promise (baseline n=127); Q2 status-chase and rework costs ran near $7,742/quarter.", "seeded_at": "2026-10-20T09:05:00Z"},
            {"panel": "current_condition", "seeded_from": {"artifact_ref": "tickets-baseline.csv (T-13 baseline run)", "tool_id": "T-13", "fields": ["descriptive.mean", "stable", "capability.cpk_index"]},
             "narrative": "Baseline: stable (zero rule-1/rule-4 signals) yet one-sided Cpk -0.96 -- the process was built to miss the promise every time, not having a bad week.", "seeded_at": "2026-10-20T09:07:00Z"},
            {"panel": "goal", "seeded_from": {"artifact_ref": CHARTER_REF, "tool_id": "T-03", "fields": ["goal"]},
             "narrative": "Cut mean resolution time to 8.0 business hours by 2026-10-31 without degrading the reopen-rate or overtime guardrails.", "seeded_at": "2026-10-20T09:08:00Z"},
            {"panel": "analysis", "seeded_from": {"artifact_ref": "s1-fishbone", "tool_id": "T-15", "fields": ["causes", "effect"]},
             "narrative": "The once-a-day triage batch (53.5% of delay tallies) and the late manager-approval request on access grants (26.8%) are the engine-verified 80.3% vital few; the Welch t confirms access grants run ~7.4h slower than the rest even though non-access tickets alone already average 23.76h against the promise.", "seeded_at": "2026-10-20T09:12:00Z"},
            {"panel": "countermeasures", "seeded_from": {"artifact_ref": "s1-solution-matrix", "tool_id": "T-18", "fields": ["ranked_fix_list"]},
             "narrative": "Assign-on-arrival dispatch rule ranked first ($0, attacks the #1 cause); pre-approved access matrix queued second; the fourth-tech hire ranked last -- capacity was never the verified cause.", "seeded_at": "2026-10-20T09:15:00Z"},
            {"panel": "results", "seeded_from": {"artifact_ref": "s1-proof", "tool_id": "T-20", "fields": ["gap", "verdict", "test_result"]},
             "narrative": "After window (n=124): mean 7.22h, threshold met (vs 12.0), weakened by the declared fall-onboarding confound (direction: could only mask the win). Goal gap recovered ~104.2%. Capability at the moment of best news: stable, Cpk 0.12 -- the mean promise is kept, ~35.5% of tickets still ran over the 8-hour line.", "seeded_at": "2026-10-20T09:20:00Z"},
            {"panel": "follow_up_control", "seeded_from": {"artifact_ref": "s1-control-plan", "tool_id": "T-22", "fields": ["monitored_items", "ocap_entries"]},
             "narrative": "I-MR chart frozen on the after window (center 7.22, limits 0.61/13.83); control plan monitors C1 weekly, the reopen guardrail, and dispatch-within-the-hour compliance itself; Naomi Castillo accepted the owner role 2026-10-12.", "seeded_at": "2026-10-20T09:24:00Z"},
            {"panel": "lessons", "seeded_from": {"artifact_ref": "s1-proof", "tool_id": "T-20", "fields": ["gap", "verdict"]},
             "narrative": "The dead end worth naming: tech capacity was investigated and ruled out early (hands-on work is only 1.9h of 26.7h) -- resisting the instinct to just hire is what let the $0 dispatch-rule fix do the work.", "seeded_at": "2026-10-20T09:26:00Z"},
        ],
        "closure": {
            "objectives_input": {"charter_baseline_value": baseline_mean, "charter_goal_value": USL, "achieved_value": statistics.fmean(after_values), "direction": "lower_is_better"},
        },
    }
    common.save_and_prescore(recorder, engine, PROJECT_ID, "T-25", "T-25", a3)
