interface Props {
  code?: string | null;
}

const STYLES: Record<string, { bg: string; text: string; label: string }> = {
  INTERN: {
    bg: "bg-role-intern/30",
    text: "text-brand-brown-darker",
    label: "Intern",
  },
  TRAINEE: {
    bg: "bg-info/15",
    text: "text-info",
    label: "Trainee",
  },
  PERMANENT: {
    bg: "bg-success/15",
    text: "text-success",
    label: "Permanent",
  },
  CONTRACT: {
    bg: "bg-warning/15",
    text: "text-warning",
    label: "Contract",
  },
};

export function CategoryBadge({ code }: Props) {
  if (!code) return <span className="text-brand-brown-light">—</span>;
  const s = STYLES[code] ?? {
    bg: "bg-brand-brown-50",
    text: "text-brand-brown-darker",
    label: code,
  };
  return (
    <span
      className={`inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded ${s.bg} ${s.text}`}
    >
      {s.label}
    </span>
  );
}
