-- 投票ログテーブルの作成
CREATE TABLE IF NOT EXISTS public.votes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  topic_id TEXT NOT NULL,
  choice_idx INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  ip_hash TEXT NOT NULL
);

-- インデックスの作成
CREATE INDEX IF NOT EXISTS idx_votes_topic_id ON public.votes(topic_id);
CREATE INDEX IF NOT EXISTS idx_votes_created_at ON public.votes(created_at);

-- Row Level Security (RLS) の有効化
ALTER TABLE public.votes ENABLE ROW LEVEL SECURITY;

-- 誰でも投票結果を読み取れるポリシー
CREATE POLICY "Allow public read access" ON public.votes
  FOR SELECT USING (true);

-- 誰でも投票をインサートできるポリシー
CREATE POLICY "Allow public insert access" ON public.votes
  FOR INSERT WITH CHECK (true);

-- クライアントのIPアドレス（x-forwarded-for ヘッダー）を取得する関数
CREATE OR REPLACE FUNCTION public.get_client_ip()
RETURNS text AS $$
DECLARE
  headers json;
  ip text;
BEGIN
  headers := current_setting('request.headers', true)::json;
  IF headers IS NOT NULL AND headers->>'x-forwarded-for' IS NOT NULL THEN
    -- x-forwarded-for は複数のIPがカンマ区切りで入ることがあるため、最初のIPを取得
    ip := split_part(headers->>'x-forwarded-for', ',', 1);
    RETURN trim(ip);
  END IF;
  RETURN 'unknown';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 投票前にIPのハッシュを設定し、同一IPの重複投票を防ぐトリガー
CREATE OR REPLACE FUNCTION public.process_vote()
RETURNS trigger AS $$
DECLARE
  client_ip text;
  hashed_ip text;
  recent_count integer;
BEGIN
  client_ip := public.get_client_ip();
  hashed_ip := md5(client_ip); -- IPアドレスをMD5でハッシュ化して保存
  new.ip_hash := hashed_ip;

  -- 過去24時間以内に同じIPから同じトピックへの投票があるかチェック
  SELECT count(*) INTO recent_count
  FROM public.votes
  WHERE topic_id = new.topic_id
    AND ip_hash = hashed_ip
    AND created_at > now() - INTERVAL '24 hours';

  IF recent_count > 0 THEN
    RAISE EXCEPTION 'You have already voted on this topic in the last 24 hours.';
  END IF;

  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- トリガーの作成
DROP TRIGGER IF EXISTS trg_process_vote ON public.votes;
CREATE TRIGGER trg_process_vote
  BEFORE INSERT ON public.votes
  FOR EACH ROW
  EXECUTE FUNCTION public.process_vote();
