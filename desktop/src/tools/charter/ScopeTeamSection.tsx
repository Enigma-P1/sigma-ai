import { Field, Panel, TextArea, TextInput } from "../../design/components";
import type { FieldFlag } from "../../design/components";
import { DynamicList } from "./DynamicList";
import type { ScopeBlock, TeamMember } from "../../api/types";

export interface ScopeTeamSectionProps {
  scope: ScopeBlock;
  onScopeChange: (v: ScopeBlock) => void;
  team: TeamMember[];
  onTeamChange: (v: TeamMember[]) => void;
  owner: TeamMember;
  onOwnerChange: (v: TeamMember) => void;
  ownerFlag?: FieldFlag;
}

const emptyMember = (): TeamMember => ({ name: "", role: "" });

/** Scope in/out, the team roster, and the process owner. */
export function ScopeTeamSection({ scope, onScopeChange, team, onTeamChange, owner, onOwnerChange, ownerFlag }: ScopeTeamSectionProps) {
  return (
    <Panel title="Scope, team, and owner">
      <Field label="In scope" required htmlFor="charter-in-scope">
        <TextArea
          id="charter-in-scope"
          data-testid="charter-scope-in"
          value={scope.in_scope}
          onChange={(e) => onScopeChange({ ...scope, in_scope: e.target.value })}
          rows={2}
        />
      </Field>
      <Field label="Out of scope" required htmlFor="charter-out-scope">
        <TextArea
          id="charter-out-scope"
          data-testid="charter-scope-out"
          value={scope.out_scope}
          onChange={(e) => onScopeChange({ ...scope, out_scope: e.target.value })}
          rows={2}
        />
      </Field>

      <Field label="Process owner" required flag={ownerFlag} helper="A real, named person -- not a placeholder like TBD or management.">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
          <TextInput
            data-testid="charter-owner-name"
            value={owner.name}
            onChange={(e) => onOwnerChange({ ...owner, name: e.target.value })}
            placeholder="Maria Ortiz"
          />
          <TextInput
            data-testid="charter-owner-role"
            value={owner.role}
            onChange={(e) => onOwnerChange({ ...owner, role: e.target.value })}
            placeholder="Line-2 supervisor"
          />
        </div>
      </Field>

      <Field label="Team" required helper="At least one member.">
        <DynamicList
          items={team}
          onChange={onTeamChange}
          makeEmpty={emptyMember}
          minItems={1}
          addLabel="+ Add team member"
          renderRow={(member, i, update) => (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
              <TextInput
                data-testid={`charter-team-${i}-name`}
                value={member.name}
                onChange={(e) => update({ ...member, name: e.target.value })}
                placeholder="Name"
              />
              <TextInput
                data-testid={`charter-team-${i}-role`}
                value={member.role}
                onChange={(e) => update({ ...member, role: e.target.value })}
                placeholder="Role"
              />
            </div>
          )}
        />
      </Field>
    </Panel>
  );
}
