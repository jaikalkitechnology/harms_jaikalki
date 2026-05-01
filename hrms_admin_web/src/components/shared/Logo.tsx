import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  variant?: "horizontal-light" | "horizontal-dark" | "icon";
  alt?: string;
}

const SRC: Record<NonNullable<LogoProps["variant"]>, string> = {
  "horizontal-light": "/branding/jaikalki-logo-horizontal-light.png",
  "horizontal-dark": "/branding/jaikalki-logo-horizontal-dark.png",
  icon: "/branding/jaikalki-icon-only-512.png",
};

export function Logo({
  className,
  variant = "horizontal-light",
  alt = "Jaikalki",
}: LogoProps) {
  return (
    <img
      src={SRC[variant]}
      alt={alt}
      className={cn("select-none", className)}
      draggable={false}
    />
  );
}
