export function ErrorBanner({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-card border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-bnpl-danger shadow-bnpl">
      {message}
    </div>
  );
}
