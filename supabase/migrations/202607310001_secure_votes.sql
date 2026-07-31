-- Canonical schema lives in data/supabase_schema.sql.
-- Keep this migration byte-for-byte equivalent by running:
--   cp data/supabase_schema.sql supabase/migrations/202607310001_secure_votes.sql

CREATE TABLE IF NOT EXISTS public.votes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  topic_id TEXT NOT NULL,
  choice_idx INTEGER NOT NULL CHECK (choice_idx >= 0 AND choice_idx < 64),
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  voter_hash TEXT
);

ALTER TABLE public.votes ADD COLUMN IF NOT EXISTS voter_hash TEXT;
UPDATE public.votes
SET voter_hash = md5(id::text) || md5('legacy:' || id::text)
WHERE voter_hash IS NULL;
ALTER TABLE public.votes ALTER COLUMN voter_hash SET NOT NULL;
ALTER TABLE public.votes DROP COLUMN IF EXISTS ip_hash;
ALTER TABLE public.votes DROP COLUMN IF EXISTS ip_addr;

CREATE INDEX IF NOT EXISTS idx_votes_topic_created ON public.votes(topic_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_votes_dedupe ON public.votes(topic_id, voter_hash, created_at DESC);
ALTER TABLE public.votes ENABLE ROW LEVEL SECURITY;
DO $$
DECLARE
  existing_policy RECORD;
BEGIN
  FOR existing_policy IN
    SELECT policyname
    FROM pg_policies
    WHERE schemaname = 'public' AND tablename = 'votes'
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.votes', existing_policy.policyname);
  END LOOP;
END;
$$;
DROP TRIGGER IF EXISTS trg_process_vote ON public.votes;
DROP FUNCTION IF EXISTS public.process_vote();
DROP FUNCTION IF EXISTS public.get_client_ip();
REVOKE ALL ON TABLE public.votes FROM anon, authenticated;

CREATE OR REPLACE FUNCTION public.cast_anonymous_vote(
  requested_topic_id TEXT,
  requested_choice_idx INTEGER,
  requested_voter_hash TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF requested_topic_id IS NULL OR length(requested_topic_id) > 100 THEN RAISE EXCEPTION 'invalid topic_id'; END IF;
  IF requested_choice_idx < 0 OR requested_choice_idx >= 64 THEN RAISE EXCEPTION 'invalid choice_idx'; END IF;
  IF requested_voter_hash IS NULL OR length(requested_voter_hash) <> 64 THEN RAISE EXCEPTION 'invalid voter_hash'; END IF;
  PERFORM pg_advisory_xact_lock(hashtext(requested_topic_id || ':' || requested_voter_hash));
  IF EXISTS (
    SELECT 1 FROM public.votes
    WHERE topic_id = requested_topic_id
      AND voter_hash = requested_voter_hash
      AND created_at > now() - interval '24 hours'
  ) THEN RETURN FALSE;
  END IF;
  INSERT INTO public.votes(topic_id, choice_idx, voter_hash)
  VALUES (requested_topic_id, requested_choice_idx, requested_voter_hash);
  RETURN TRUE;
END;
$$;

CREATE OR REPLACE FUNCTION public.get_vote_counts(requested_topic_id TEXT)
RETURNS TABLE(choice_idx INTEGER, vote_count BIGINT)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT votes.choice_idx, count(*)::BIGINT
  FROM public.votes
  WHERE votes.topic_id = requested_topic_id
  GROUP BY votes.choice_idx
  ORDER BY votes.choice_idx;
$$;

REVOKE ALL ON FUNCTION public.cast_anonymous_vote(TEXT, INTEGER, TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.get_vote_counts(TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.cast_anonymous_vote(TEXT, INTEGER, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.get_vote_counts(TEXT) TO service_role;
