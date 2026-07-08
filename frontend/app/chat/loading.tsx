import { Skeleton } from "@/components/ui/skeleton";

export default function ChatLoading() {
  return (
    <div className="mx-auto max-w-3xl space-y-4 p-6">
      <Skeleton className="h-12 w-2/3" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-12 w-1/2" />
    </div>
  );
}
