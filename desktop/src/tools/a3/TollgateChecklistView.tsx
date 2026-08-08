import { Panel } from "../../design/components";
import { CLIENT_TOLLGATE_QUESTIONS } from "./a3Checks";
import type { TollgateAnswer, TollgatePhase, TollgateQuestion } from "../../api/types";

export interface TollgateChecklistViewProps {
  phase: TollgatePhase;
  serverQuestions: TollgateQuestion[] | null; // authoritative once a version has round-tripped
  answers: TollgateAnswer[];
  onAnswer: (answer: TollgateAnswer) => void;
}

/** One phase's tollgate checklist -- this engine's own original-wording
 * standard Champion questions (client mirror before the first save,
 * server-echoed after -- CLIENT_TOLLGATE_QUESTIONS' own docstring). */
export function TollgateChecklistView({ phase, serverQuestions, answers, onAnswer }: TollgateChecklistViewProps) {
  const questions = serverQuestions && serverQuestions.length > 0 ? serverQuestions : CLIENT_TOLLGATE_QUESTIONS[phase];
  const byId = new Map(answers.map((a) => [a.question_id, a]));

  return (
    <Panel title={`${phase} tollgate`} collapsible defaultOpen={false}>
      <ul className="sigma-a3-tollgate-list" data-testid={`a3-tollgate-${phase}`}>
        {questions.map((q) => {
          const a = byId.get(q.question_id);
          return (
            <li key={q.question_id}>
              <label>
                <input
                  type="checkbox" data-testid={`a3-tollgate-${phase}-${q.question_id}-answered`} checked={a?.answered ?? false}
                  onChange={(e) => onAnswer({ question_id: q.question_id, answered: e.target.checked, response: a?.response ?? "", evidence_ref: a?.evidence_ref ?? null })}
                />
                {q.text}
              </label>
              <input
                className="sigma-input" placeholder="response / evidence" value={a?.response ?? ""}
                onChange={(e) => onAnswer({ question_id: q.question_id, answered: a?.answered ?? false, response: e.target.value, evidence_ref: a?.evidence_ref ?? null })}
              />
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}
