import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Public routes that don't require auth
const PUBLIC_ROUTES = ["/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public routes always
  if (PUBLIC_ROUTES.some((r) => pathname.startsWith(r))) {
    return NextResponse.next();
  }

  // For protected routes (/chat, /documents), we rely on client-side auth check
  // (localStorage tokens are not accessible in middleware — handled in layout.tsx)
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api).*)"],
};
