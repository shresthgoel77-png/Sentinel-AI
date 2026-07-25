import SectionHeading from './SectionHeading'

const TAKEAWAYS = [
  {
    title: 'Catch malicious prompts before they reach the model',
    body: 'Jailbreak attempts are screened at the door, not after they\'ve already influenced model behavior.',
  },
  {
    title: 'Catch sensitive information before it leaves the model',
    body: 'Outbound responses are scanned for secrets so a single bad output never reaches the user.',
  },
  {
    title: 'Give teams real-time visibility into AI risk',
    body: 'A live dashboard turns invisible model behavior into something a security team can actually monitor.',
  },
]

export default function JudgesSection() {
  return (
    <section id="judges" className="scroll-mt-24 border-t border-edge/60 bg-surface/30 py-20 sm:py-28">
      <div className="mx-auto max-w-4xl px-6">
        <SectionHeading align="center" eyebrow="Why This Matters" title="AI agents now touch real, sensitive systems" />

        <p className="mx-auto mt-6 max-w-2xl text-center text-base leading-relaxed text-muted">
          As AI agents get plugged into databases, internal docs, and customer records, two risks grow
          together: prompt attacks that manipulate behavior, and data leakage that exposes what the model
          can see. AI Shield is a small proof of concept for the security layer that sits between the two.
        </p>

        <div className="mt-14 grid gap-5 sm:grid-cols-3">
          {TAKEAWAYS.map((item, i) => (
            <div key={item.title} className="panel p-6">
              <span className="font-mono text-2xl font-semibold text-violet">{String(i + 1).padStart(2, '0')}</span>
              <h3 className="mt-3 font-display text-base font-semibold text-white">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{item.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
