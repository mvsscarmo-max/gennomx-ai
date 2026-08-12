import { NextResponse, type NextRequest } from "next/server";
import { jwtVerify } from "jose";
import { withBasePath } from "@/lib/base-path";
import { AUTH_COOKIE_NAME } from "@/lib/auth-token";

// Mirrors backend `require_admin` (app/auth/dependencies.py): these routes only
// render usable data for the admin role, so non-admins are redirected before
// hitting a page that would otherwise just show 403s from every API call.
const ADMIN_ONLY_PATHS = ["/governance", "/security"];

function isAdminOnlyPath(pathname: string): boolean {
  return ADMIN_ONLY_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));
}

export async function middleware(request: NextRequest) {
  if (process.env.NODE_ENV !== "production" && process.env.E2E_BYPASS_AUTH === "true") {
    return NextResponse.next({ request });
  }
  const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (!token) return NextResponse.redirect(new URL(withBasePath("/login"), request.url));
  const secret = process.env.AUTH_JWT_SECRET;
  const issuer = process.env.AUTH_JWT_ISSUER ?? "gennomx-ai";
  const audience = process.env.AUTH_JWT_AUDIENCE ?? "gennomx-dashboard";
  if (!secret) return NextResponse.redirect(new URL(withBasePath("/login"), request.url));
  let payloadRole = "readonly";
  try {
    const { payload } = await jwtVerify(token, new TextEncoder().encode(secret), {
      issuer,
      audience,
    });
    payloadRole = typeof payload.role === "string" ? payload.role : "readonly";
  } catch {
    return NextResponse.redirect(new URL(withBasePath("/login"), request.url));
  }

  const role = payloadRole;
  if (role !== "admin" && isAdminOnlyPath(request.nextUrl.pathname)) {
    return NextResponse.redirect(new URL(withBasePath("/"), request.url));
  }

  return NextResponse.next({ request });
}

export const config = { matcher: ["/((?!login|_next/static|_next/image|favicon.ico).*)"] };
