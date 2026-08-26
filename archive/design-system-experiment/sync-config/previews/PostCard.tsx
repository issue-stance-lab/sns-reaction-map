import { PostCard } from 'issue-stance-ds';

export function WithQuote() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8', maxWidth: 640 }}>
      <PostCard
        num={1}
        topic="9条・自衛隊明記"
        stance="賛成"
        stanceVariant="support"
        summary="自衛隊の憲法上の地位を明確化すべきという立場から改憲を支持。現行解釈の曖昧さが安全保障上のリスクだと指摘。"
        quote="自衛隊が違憲かもしれないという状態を放置するのは国として無責任だ。明記することで隊員の士気も上がる。"
        reason="改憲支持の典型的な論拠。安全保障上の必要性を根拠とする。"
        postedAt="2026-06-18"
        likes={142}
        retweets={38}
        href="#"
      />
    </div>
  );
}

export function OppositionCard() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8', maxWidth: 640 }}>
      <PostCard
        num={2}
        topic="緊急事態条項"
        stance="反対"
        stanceVariant="oppose"
        summary="緊急事態条項の新設は権力集中と人権制限のリスクがあるとして強く反対する立場。"
        quote="緊急事態を口実に議会機能を停止させる条項は民主主義の根幹を揺るがす。絶対に許せない。"
        reason="緊急事態条項への反対意見。民主主義・人権上の懸念が主な根拠。"
        postedAt="2026-06-17"
        likes={89}
        retweets={24}
      />
    </div>
  );
}

export function Cautious() {
  return (
    <div style={{ padding: 16, background: '#f4f6f8', maxWidth: 640 }}>
      <PostCard
        num={3}
        topic="国民投票法・広告規制"
        stance="手続き重視"
        stanceVariant="cautious"
        summary="改憲の是非より国民投票の公正性を先に確保すべきという立場。広告規制の欠如を問題視。"
        reason="改憲の賛否ではなく手続きの公平性を重視するカテゴリ。"
        postedAt="2026-06-16"
        likes={204}
        retweets={67}
      />
    </div>
  );
}
