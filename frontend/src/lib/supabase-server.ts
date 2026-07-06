import "server-only";

import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function getServerAccessToken(): Promise<string | undefined> {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return undefined;

  const cookieStore = await cookies();
  const supabase = createServerClient(url, key, {
    cookies: {
      getAll: () => cookieStore.getAll(),
      setAll: () => {
        // Session refresh cookies are written by middleware. Server Components are read-only.
      },
    },
  });
  const { data: userData } = await supabase.auth.getUser();
  if (!userData.user) return undefined;
  const { data: sessionData } = await supabase.auth.getSession();
  return sessionData.session?.access_token;
}
