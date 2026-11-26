type SkeletonProps = {
  rows?: number;
  className?: string;
};

export function Skeleton({ rows = 3, className = "" }: SkeletonProps) {
  return (
    <div className={`space-y-2 ${className}`} role="status" aria-label="Loading">
      {Array.from({ length: rows }, (_, index) => (
        <div
          key={index}
          className="h-4 animate-pulse rounded bg-slate-200"
          style={{ width: `${100 - index * (45 / Math.max(rows, 1))}%` }}
        />
      ))}
    </div>
  );
}
