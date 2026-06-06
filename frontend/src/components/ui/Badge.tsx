export function Badge({ className, children }: { className: string; children: React.ReactNode }) {
  return <span className={className}>{children}</span>;
}
