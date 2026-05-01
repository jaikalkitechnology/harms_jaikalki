import { Logo } from "@/components/shared/Logo";

export function LoadingScreen({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="min-h-screen grid place-items-center bg-surface-cream">
      <div className="flex flex-col items-center gap-6">
        <div className="relative">
          <Logo variant="icon" className="h-20 w-20 animate-pulse-glow" />
        </div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-brown-light">
          {label}
        </div>
      </div>
    </div>
  );
}

export function Spinner({ className = "" }: { className?: string }) {
  return (
    <div
      className={`inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent ${className}`}
      role="status"
      aria-label="Loading"
    />
  );
}

export function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-4 rounded bg-brand-brown-50"
          style={{ width: `${100 - i * 12}%` }}
        />
      ))}
    </div>
  );
}
