import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { jwtVerify } from "jose";

// Public routes that don't require auth
const PUBLIC_ROUTES = ["/login", "/register"];

// Same HS256 secret the FastAPI backend signs access_token cookies with —
// must be set on the frontend deployment too so middleware can verify the
// signature without a round-trip to the backend.
const JWT_SECRET = process.env.JWT_SECRET;

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (PUBLIC_ROUTES.some((r) => pathname.startsWith(r))) {
    return NextResponse.next();
  }

  const token = request.cookies.get("access_token")?.value;

  if (!token || !JWT_SECRET) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  try {
    await jwtVerify(token, new TextEncoder().encode(JWT_SECRET));
    return NextResponse.next();
  } catch {
    // Expired or invalid signature — clear the stale cookie and bounce to login.
    const response = NextResponse.redirect(new URL("/login", request.url));
    response.cookies.delete("access_token");
    return response;
  }
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api).*)"],
};
