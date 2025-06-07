export const Skeleton = () => (
  <div className="p-4 space-y-4">
    <div className="h-8 bg-gray-200 rounded animate-pulse" />
    {[...Array(2)].map((_, i) => (
      <div key={i} className="space-y-2">
        <div className="h-4 bg-gray-100 rounded w-1/2 animate-pulse" />
        <div className="h-10 bg-gray-100 rounded animate-pulse" />
      </div>
    ))}
  </div>
);