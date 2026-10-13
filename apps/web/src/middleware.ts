import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const role = request.cookies.get("omni_role")?.value;
  const isLoggedIn = request.cookies.get("omni_logged_in")?.value === "true";

  // 1. Unauthenticated users trying to access protected areas
  if (!isLoggedIn) {
    if (pathname.startsWith("/app")) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
    if (pathname.startsWith("/merchant")) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  // 2. Authenticated user visiting auth pages (/login, /register) -> redirect to respective home
  if (isLoggedIn && (pathname === "/login" || pathname === "/register")) {
    if (role === "merchant") {
      return NextResponse.redirect(new URL("/merchant", request.url));
    }
    return NextResponse.redirect(new URL("/app", request.url));
  }

  // 3. Role-based isolation
  // Shoppers cannot access merchant ops portal
  if (isLoggedIn && role === "user" && pathname.startsWith("/merchant")) {
    return NextResponse.redirect(new URL("/app", request.url));
  }

  // Merchants visiting shopper mission home redirected to merchant ops
  if (isLoggedIn && role === "merchant" && pathname.startsWith("/app")) {
    return NextResponse.redirect(new URL("/merchant", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*", "/merchant/:path*", "/login", "/register"],
};
