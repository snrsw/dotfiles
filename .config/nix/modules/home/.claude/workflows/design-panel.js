export const meta = {
  name: 'design-panel',
  description: 'Generate independent design candidates for a question, judge them through distinct lenses, and synthesize the winner',
  whenToUse: 'Design or architecture decisions with no objective ground truth — where one attempt would anchor on the first idea.',
  phases: [
    { title: 'Propose', detail: 'independent candidates from distinct angles' },
    { title: 'Judge', detail: 'each judge scores all candidates through one lens' },
    { title: 'Synthesize', detail: 'winner improved with the best ideas from runners-up' },
  ],
}

const question = typeof args === 'string' ? args : (args && args.question) || ''
if (!question) {
  throw new Error('Pass the design question as args: Workflow({name: "design-panel", args: "<question>"})')
}

const ANGLES = [
  'simplest-thing-that-works: minimize moving parts and future maintenance',
  'risk-first: minimize blast radius, favor reversibility and isolation',
  'user-first: optimize the day-to-day experience of whoever uses the result',
]

const LENSES = [
  'correctness and simplicity',
  'reversibility and risk',
  'fit with the existing codebase and its conventions',
]

phase('Propose')
const proposals = await parallel(ANGLES.map((angle, i) => () =>
  agent(
    `Design question:\n${question}\n\n` +
    `Propose ONE concrete design from this angle: ${angle}.\n` +
    'If a repository is relevant, explore it first and ground the design in what exists.\n' +
    'Return: the design (concrete, with tradeoffs), key assumptions, and what would make it fail.',
    { label: `propose:${i + 1}`, phase: 'Propose' },
  )))

const candidates = proposals.filter(Boolean)
if (candidates.length === 0) throw new Error('No proposals produced')

phase('Judge')
const SCORE = {
  type: 'object',
  additionalProperties: false,
  required: ['scores', 'reasoning'],
  properties: {
    scores: {
      type: 'array',
      description: 'One score 0-100 per candidate, in candidate order',
      items: { type: 'number' },
    },
    reasoning: { type: 'string' },
  },
}

const candidateSheet = candidates
  .map((c, i) => `--- Candidate ${i + 1} ---\n${c}`)
  .join('\n\n')

const verdicts = await parallel(LENSES.map(lens => () =>
  agent(
    `Design question:\n${question}\n\nCandidates:\n${candidateSheet}\n\n` +
    `Judge ONLY through this lens: ${lens}.\n` +
    'Score each candidate 0-100 (array order = candidate order) and explain briefly. ' +
    'Be willing to score low; do not cluster scores to be polite.',
    { label: `judge:${lens.split(' ')[0]}`, phase: 'Judge', schema: SCORE },
  )))

const usableVerdicts = verdicts.filter(Boolean)
const totals = candidates.map((_, i) =>
  usableVerdicts.reduce((sum, v) => sum + (v.scores[i] || 0), 0))
const winner = totals.indexOf(Math.max(...totals))
log(`Winner: candidate ${winner + 1} (lens totals: ${totals.join(', ')})`)

phase('Synthesize')
const runnersUp = candidates.filter((_, i) => i !== winner).join('\n\n---\n\n')
const judgeNotes = usableVerdicts.map(v => v.reasoning).join('\n')

return await agent(
  `Design question:\n${question}\n\n` +
  `Winning design (candidate ${winner + 1}):\n${candidates[winner]}\n\n` +
  `Runner-up designs:\n${runnersUp}\n\n` +
  `Judge reasoning:\n${judgeNotes}\n\n` +
  'Produce the final recommended design: the winner, improved with any clearly better ideas ' +
  'from the runners-up. Include the assumptions it rests on, explicit non-goals, and ' +
  'checkable acceptance criteria.',
  { label: 'synthesize', phase: 'Synthesize' },
)
