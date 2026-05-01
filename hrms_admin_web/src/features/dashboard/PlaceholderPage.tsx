interface Props {
  title: string;
  phase: string;
  description: string;
}

export default function PlaceholderPage({ title, phase, description }: Props) {
  return (
    <div className="max-w-2xl">
      <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
        {phase}
      </div>
      <h2 className="font-display text-3xl font-bold text-brand-brown-darker mt-1">
        {title}
      </h2>
      <p className="mt-3 text-brand-brown-light">{description}</p>
    </div>
  );
}
