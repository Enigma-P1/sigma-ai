import { Button, Field, TextInput, VerdictBanner } from "../../design/components";
import { draftLowestCategory, draftTotal } from "./fiveSLogic";
import type { AuditRound } from "../../api/types";
import { FIVE_S_CATEGORY_LABELS } from "../../api/types";

export interface AuditRoundFormProps {
  round: AuditRound;
  onChange: (patch: Partial<AuditRound>) => void;
  onRemove: () => void;
  onPhotoSelected: (file: File) => void;
  uploading: boolean;
}

/** One 5S audit round: date/area, five 0-5 category scores with notes,
 * photo upload (reuses the floor-plan image store), and the action tied
 * to this round's lowest-scoring category. */
export function AuditRoundForm({ round, onChange, onRemove, onPhotoSelected, uploading }: AuditRoundFormProps) {
  return (
    <div className="sigma-fives-round" data-testid={`fives-round-${round.round_id}`}>
      <div className="sigma-fives-round__header">
        <Field label="Date" htmlFor={`fives-${round.round_id}-date`}><TextInput id={`fives-${round.round_id}-date`} type="date" value={round.date} onChange={(e) => onChange({ date: e.target.value })} /></Field>
        <Field label="Area" htmlFor={`fives-${round.round_id}-area`}><TextInput id={`fives-${round.round_id}-area`} data-testid={`fives-${round.round_id}-area`} value={round.area} onChange={(e) => onChange({ area: e.target.value })} /></Field>
        <Button variant="danger" size="sm" onClick={onRemove}>Remove round</Button>
      </div>

      <div className="sigma-fives-scores">
        {round.scores.map((s) => (
          <Field key={s.category} label={`${FIVE_S_CATEGORY_LABELS[s.category]} (0-5)`} htmlFor={`fives-${round.round_id}-${s.category}`}>
            <input
              id={`fives-${round.round_id}-${s.category}`} data-testid={`fives-${round.round_id}-${s.category}-score`}
              type="number" min={0} max={5} value={s.score}
              onChange={(e) => onChange({ scores: round.scores.map((x) => (x.category === s.category ? { ...x, score: Number(e.target.value) } : x)) })}
            />
            <TextInput
              placeholder="note" value={s.note}
              onChange={(e) => onChange({ scores: round.scores.map((x) => (x.category === s.category ? { ...x, note: e.target.value } : x)) })}
            />
          </Field>
        ))}
      </div>

      <VerdictBanner tone="neutral" headline={`Total ${draftTotal(round)}/25 -- lowest: ${FIVE_S_CATEGORY_LABELS[draftLowestCategory(round)]}`} />

      <Field label="Photo" helper="A round can carry more than one -- physical state should carry the score.">
        <input type="file" accept=".png,.jpg,.jpeg" data-testid={`fives-${round.round_id}-photo-input`} onChange={(e) => { const f = e.target.files?.[0]; if (f) onPhotoSelected(f); }} />
      </Field>
      {uploading && <p>Uploading…</p>}
      {round.photos.length > 0 && <p data-testid={`fives-${round.round_id}-photo-count`}>{round.photos.length} photo(s) attached</p>}

      <Field label={`Action for the lowest category (${FIVE_S_CATEGORY_LABELS[draftLowestCategory(round)]})`} htmlFor={`fives-${round.round_id}-action`}>
        <TextInput id={`fives-${round.round_id}-action`} data-testid={`fives-${round.round_id}-action`} value={round.improvement_action} onChange={(e) => onChange({ improvement_action: e.target.value })} />
      </Field>
      <Field label="Action owner" htmlFor={`fives-${round.round_id}-action-owner`}>
        <TextInput id={`fives-${round.round_id}-action-owner`} value={round.improvement_action_owner} onChange={(e) => onChange({ improvement_action_owner: e.target.value })} />
      </Field>
    </div>
  );
}
