import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const TOPIC_CHOICES: Record<string, number> = {
  "ai-copyright-issue-stance-v1": 21,
  "bike-blue-ticket-issue-stance-v1": 18,
  "bukatsu-chiiki-issue-stance-v1": 21,
  "constitutional-amendment-issue-stance-v1": 24,
  "consumption-tax-cut-issue-stance-v1": 28,
  "elderly-license-revocation-issue-stance-v1": 18,
  "fukushuto-issue-stance-v1": 21,
  "henoko-student-accident-issue-stance-v1": 18,
  // v1 は論点7つ×立場4。論点を正典の分類に揃えて6つにしたため v2 へ移行した。
  // 集計は選択肢インデックス依存なので、v1 の票を v2 に引き継ぐことはできない。
  "koshitsu-tenpakai-issue-stance-v1": 28,
  "koshitsu-tenpakai-issue-stance-v2": 24,
  "school-nickname-ban-issue-stance-v1": 18,
  "takaichi-issue-stance-v1": 15,
};

function corsHeaders(request: Request): HeadersInit {
  const origin = request.headers.get("origin") || "";
  const configured = (Deno.env.get("VOTE_ALLOWED_ORIGINS") ||
    "https://sns-reaction-map.jp,https://issue-stance-lab.github.io,http://localhost:8000,http://127.0.0.1:8000")
    .split(",")
    .map((value) => value.trim());
  return {
    "Access-Control-Allow-Origin": configured.includes(origin) ? origin : configured[0],
    "Access-Control-Allow-Headers": "authorization, apikey, content-type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Vary": "Origin",
  };
}

function json(request: Request, body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(request), "Content-Type": "application/json; charset=utf-8" },
  });
}

function clientIp(request: Request): string | null {
  const forwarded = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
  return forwarded || request.headers.get("cf-connecting-ip") || request.headers.get("x-real-ip");
}

async function hmacHex(secret: string, value: string): Promise<string> {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const bytes = new Uint8Array(await crypto.subtle.sign("HMAC", key, encoder.encode(value)));
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function validTopic(topicId: unknown): topicId is string {
  return typeof topicId === "string" && Object.hasOwn(TOPIC_CHOICES, topicId);
}

Deno.serve(async (request) => {
  if (request.method === "OPTIONS") return new Response("ok", { headers: corsHeaders(request) });
  if (request.method !== "GET" && request.method !== "POST") return json(request, { error: "method_not_allowed" }, 405);

  const origin = request.headers.get("origin") || "";
  const allowedOrigins = (Deno.env.get("VOTE_ALLOWED_ORIGINS") ||
    "https://sns-reaction-map.jp,https://issue-stance-lab.github.io,http://localhost:8000,http://127.0.0.1:8000")
    .split(",")
    .map((value) => value.trim());
  if (origin && !allowedOrigins.includes(origin)) return json(request, { error: "origin_not_allowed" }, 403);

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const hashSecret = Deno.env.get("VOTE_HASH_SECRET");
  if (!supabaseUrl || !serviceKey || !hashSecret || hashSecret.length < 32) {
    console.error("Missing Supabase credentials or a 32+ character VOTE_HASH_SECRET");
    return json(request, { error: "server_not_configured" }, 503);
  }

  const admin = createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  let topicId: unknown;
  let choiceIdx: unknown;
  if (request.method === "GET") {
    topicId = new URL(request.url).searchParams.get("topic_id");
  } else {
    try {
      const body = await request.json();
      topicId = body.topic_id;
      choiceIdx = body.choice_idx;
    } catch {
      return json(request, { error: "invalid_json" }, 400);
    }
  }

  if (!validTopic(topicId)) return json(request, { error: "invalid_topic" }, 400);

  let accepted: boolean | undefined;
  if (request.method === "POST") {
    if (!Number.isInteger(choiceIdx) || (choiceIdx as number) < 0 || (choiceIdx as number) >= TOPIC_CHOICES[topicId]) {
      return json(request, { error: "invalid_choice" }, 400);
    }
    const ip = clientIp(request);
    if (!ip) return json(request, { error: "client_ip_unavailable" }, 503);
    const voterHash = await hmacHex(hashSecret, ip);
    const { data, error } = await admin.rpc("cast_anonymous_vote", {
      requested_topic_id: topicId,
      requested_choice_idx: choiceIdx,
      requested_voter_hash: voterHash,
    });
    if (error) {
      console.error("cast_anonymous_vote failed", error);
      return json(request, { error: "vote_failed" }, 500);
    }
    accepted = data === true;
  }

  const { data: rows, error: countError } = await admin.rpc("get_vote_counts", {
    requested_topic_id: topicId,
  });
  if (countError) {
    console.error("get_vote_counts failed", countError);
    return json(request, { error: "count_failed" }, 500);
  }

  const counts: Record<string, number> = {};
  for (const row of rows || []) counts[String(row.choice_idx)] = Number(row.vote_count);
  return json(request, {
    accepted,
    duplicate: request.method === "POST" ? !accepted : undefined,
    counts,
  });
});
