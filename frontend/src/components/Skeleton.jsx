export function SkeletonBlock({ className = "" }) {
  return <div className={`skeleton rounded-lg animate-shimmer ${className}`} />;
}

export function NeighborhoodCardSkeleton() {
  return (
    <div className="border border-slate-200 dark:border-slate-800 rounded-2xl bg-white dark:bg-slate-900 p-5 flex items-center justify-between gap-4">
      <div className="space-y-2 flex-1">
        <SkeletonBlock className="h-4 w-40" />
        <SkeletonBlock className="h-3 w-24" />
      </div>
      <div className="space-y-2">
        <SkeletonBlock className="h-3 w-20 ml-auto" />
        <SkeletonBlock className="h-5 w-28" />
      </div>
    </div>
  );
}
