"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/chat/AppShell";
import { useAuth } from "@/lib/hooks/useAuth";
import { Skeleton } from "@/components/ui/skeleton";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, loading, isAuthenticated, logout } = useAuth();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    } else if (!loading && isAuthenticated && !user?.is_admin) {
      router.replace("/chat");
    }
  }, [loading, isAuthenticated, user, router]);

  if (loading) {
    return (
      <div className="flex h-screen">
        <div className="w-64 space-y-3 border-r p-4">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-3/4" />
        </div>
        <div className="flex-1" />
      </div>
    );
  }

  if (!isAuthenticated || !user?.is_admin) return null;

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  return (
    <AppShell onLogout={handleLogout} userName={user?.email} isAdmin={user?.is_admin}>
      {children}
    </AppShell>
  );
}
