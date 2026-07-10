import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { withBasePath } from "@/lib/base-path";

type CookieUpdate = {
  name: string;
  value: string;
  options?: Parameters<NextResponse["cookies"]["set"]>[2];
};

// Mirrors backend `require_admin` (app/auth/dependencies.py): these routes only
// render usable data for the "admin" gennomx_role, so non-admins are redirected
// before hitting a page that would otherwise just show 403s from every API call.
const ADMIN_ONLY_PATHS = ["/governance", "/security"];

function isAdminOnlyPath(pathname: string): boolean {
  return ADMIN_ONLY_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));
}

export async function middleware(request: NextRequest) {
  if (process.env.NODE_ENV !== "production" && process.env.E2E_BYPASS_AUTH === "true") {
    return NextResponse.next({ request });
  }
  let response = NextResponse.next({ request });
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return NextResponse.redirect(new URL(withBasePath("/login"), request.url));
  const supabase = createServerClient(url, key, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (cookies: CookieUpdate[]) => {
        cookies.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        cookies.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    },
  });
  const { data } = await supabase.auth.getUser();
  if (!data.user) return NextResponse.redirect(new URL(withBasePath("/login"), request.url));

  const role = data.user.app_metadata?.gennomx_role ?? "readonly";
  if (role !== "admin" && isAdminOnlyPath(request.nextUrl.pathname)) {
    return NextResponse.redirect(new URL(withBasePath("/"), request.url));
  }

  return response;
}

export const config = { matcher: ["/((?!login|_next/static|_next/image|favicon.ico).*)"] };
