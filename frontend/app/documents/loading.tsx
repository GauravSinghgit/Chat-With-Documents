import { Skeleton } from "@/components/ui/skeleton";

export default function DocumentsLoading() {
  return (
    <div className="space-y-4 p-6">
      <Skeleton className="h-8 w-48" />
      {[...Array(4)].map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  );
}
