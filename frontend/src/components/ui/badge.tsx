import { cn } from "@/lib/utils";

type BadgeVariant = "rose" | "slate" | "success" | "warning" | "danger" | "info";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variants: Record<BadgeVariant, string> = {
  rose: "bg-brand-rose/10 text-brand-rose-dark",
  slate: "bg-slate-100 text-slate-600",
  success: "bg-success-light text-success",
  warning: "bg-warning-light text-warning",
  danger: "bg-danger-light text-danger",
  info: "bg-info-light text-info",
};

export function Badge({ variant = "slate", children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-badge text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
