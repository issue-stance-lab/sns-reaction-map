# 皇室典範：改正対象と継承方針を分ける基準 v5

2026-09-09。v4の既存5例独立検証後、含意の必須性・保存形式の境界を明文化した基準。旧v1/v2/v3/v4・旧判断を保持し、今回の独立判断の保存後は本文書を変更しない。結果・検証範囲は別報告へ記録する。原本・採用台帳・公開分類器への適用と782件の再開は対象外。

## 判断の順序

1. 引用・記事の主張と投稿者の評価を分ける。投稿中の事実主張の真偽は今回認定しない。
2. 本人が肯定・否定している命題を特定する。「何が正しいか」「何が実現できるか」と「どの制度を採るべきか」を区別する。
3. 改正案への評価と継承資格・候補者への評価を独立に保存する。一方から他方を埋めない。
4. 根拠が欠ける部分だけunknownにし、欠落箇所と必要な追加文脈を残す。

## 改正案への賛否

`reform_target`は本人が制度変更として評価・要求した対象。current_package（本文内で今回の案全体と特定）/ specific_provision（改正措置）/ alternative_reform（別の制度変更要求）/ general_reform（対象案を特定しない改正自体）/ unexpressed / unknown。

- 記事・第三者・比較の対象として改正が出るだけでは本人のreform_targetに入れない。必要なら`mentioned_reform_target`へ自由記述する。
- 改正を後押しする比較論法への批判は、その論法への評価。制度内容や変更への本人の賛否がなければreform_target=unexpressed。賛成派・反対派の論法批判を反対の政策選好へ転記しない。
- 過去の養子や継承手続の正統性の擁護は歴史的評価。現在・将来の制度措置への明示的な適用要求がない限りspecific_provisionに入れない。
- 女性天皇等の過去の正統性、または現在・将来の資格を肯定していても、法律を変える要求がなければalternative_reformとはしない。明示された改正要求と実現したい候補・制度が結び付く場合に別案として保存する。

`current_package_stance`はsupport / oppose / mixed / unexpressed / unknown。今回の改正案全体への本人の評価だけを保存する。別案要求・条項賛否・継承方針から今回案の賛否を補わない。mixedは案全体への両義的評価がある場合。異なる条項に賛否が分かれるだけならprovisionsに分け、全体の結論がなければunexpressed（v1の条項混在からmixedへ集約する規則を置換）。

`provisions`は本人が採用・不採用を評価した、具体的な仕組み・資格規定等の改正措置の `{target, stance}` 配列。候補者の即位実現という目的だけで手段が書かれていない改正要求はreform_target=alternative_reformと主論点に保存し、provisionsへ複写しない。歴史的記述や成否予測だけも入れない。provisions[].stanceはsupport / oppose / mixed / unknown。support/opposeはその措置を採る/採らないという本人の評価、mixedは同一の措置に両義的評価が明示された場合、unknownは具体措置への評価が始まっているが帰属や結論が欠ける場合。単なる言及・成否予測は空配列に保ち、賛否を作らない。措置は肯定形で具体的に記述し、否定表現によるsupport/opposeの反転を機械的な不一致にしない。

## 継承方針の独立項目

`succession`は現在・将来に採る資格規則と即位希望の欄である。過去に存在した制度・人物が正統だったという評価は含めない。時点をまたぐ明示的な採用・適用の主張がある場合だけ、この欄へ保存する。次の5項目を個別保存し、値はsupport / oppose / mixed / unexpressed / unknownとする。

| 項目 | 評価する命題 |
| --- | --- |
| male_line_only | 継承資格を父系血統だけに限定する |
| male_only | 天皇本人の性別を男性だけに限定する |
| female_sovereign | 現在・将来、女性が天皇となる資格を認める |
| female_line | 母方を通じて皇統に連なる者の継承資格を認める |
| named_successor_aiko | 愛子さま本人の即位を支持する |

- 女性天皇支持は父系限定反対でも女系支持でもない。父系限定支持は男性限定支持ではない。集団批判からどの資格規則への反対かを補わない。
- 本人の愛子さま即位支持は現在・将来の女性天皇資格支持を含む。一般にも、現在・将来の女性資格を認めるsupportと同じ時点・制度範囲の男性限定規則は両立しないためmale_only=opposeを必ず同時に保存する。この含意は過去の正統性擁護には適用しない。血統の限定・母系資格へは拡張しない。
- 歴代の女性天皇の存在や「正統な伝統だった」という擁護は、積極的な評価であってもまずhistorical_legitimacy/affirmed/time_scope=historicalへ保存する。「今後も女性の資格を認める」「現制度は女性を排除すべきでない」等、現在・将来への適用・選好を本人が明示していなければfemale_sovereignとmale_onlyはunexpressed。男子のみの将来の安定性を否定する論証が隣接するだけでは、その明示の代用にしない。過去に正統だったという主張と、今後も採るべきだという主張を分ける。
- 男系を維持できるという実現可能性や歴史的手続の擁護だけでは、父系以外を排除する規則male_line_onlyへの支持は補わない。

## 賛否以外の評価

`other_evaluations`へ `{kind, target, assessment, time_scope}` を保存する。time_scopeはhistorical / present_or_future / unspecified。過去の人物・制度を正統とする主張はhistorical、現在・将来の成否や選好を論じる主張はpresent_or_future、時点を固定できない比較論法等はunspecified。kindはargument_validity（比較・論法）/ historical_legitimacy（過去の手続の正統性）/ feasibility（成否・実現可能性）/ tradition（継承観の伝統としての評価）。assessmentはaffirmed / denied / mixed / unknown。これは政策の賛否ラベルではない。過去の伝統の正統性を述べる同一命題はhistorical_legitimacyで代表し、traditionへ重複させなくてよい。独立比較では主な評価対象・評価の方向・時点を照合し、補助的な論法批判の記録数や自由文の表記差は政策賛否の相違と別計数にする。

「成立しない」「安定継承は不可能」はfeasibility/deniedであり、それだけで制度反対を作らない。別の文章で本人が制度への賛否や資格の正統性を表明していれば、その文章を根拠に別途保存する。否定的な人物評価も制度反対の代用にしない。

## 未表明と不明を区別する

- unexpressed：保存された本文に、その対象への本人の賛否・要求がない。将来見つかるかもしれない続きは推測しない。
- unknown：その対象について本人の評価が進行中だが、文末省略や帰属不足で方向・成立を決められない。`unknown_fields`で対象を列挙し、何が足りないか理由に書く。
- 文末の「だけど」で結論が欠け、本人の意見の成立自体を確定できないときはis_opinion=null、uncertain=true、evidence_sufficient=false。引用と比較する本人の部分が識別できるならattribution=mixedを使う。境界そのものが不明な場合だけunknown。
- unknownを周辺項目へ連鎖させない。女性天皇の議論に関する未完の比較なら、評価未完のfemale_sovereignをunknownにできるが、言及のない男子限定・父系限定・母系資格・特定候補にはunexpressedを保存する。今回案全体の評価に踏み込んでいなければcurrent_package_stanceもunexpressed。
- 末尾に矢印等があっても、すでに完結した本人の論法批判までunknownに戻さない。

## 非公開の保存形式と比較

型を固定する。is_relevantはbool、is_opinionはboolまたはnull、attributionはauthor / third_party_only / mixed / unknown。authorは本人が説明・評価している文、third_party_onlyは第三者発言・見出し等の共有だけ、mixedは識別できる引用・第三者発言と本人の判断・比較の両方、unknownは発言の帰属を区切れない場合。本人が外国制度や歴史について説明するだけではmixedにしない。main_issueは主眼を示す短い自由文で、過去の制度なら過去と明記し、既存の分類番号へ強制対応させない。mentioned_reform_targetとother_successionは文字列またはnull（非該当はnull、空配列は使わない）。provisionsとother_evaluationsとunknown_fieldsは配列で非該当は[]。unknown_fieldsはis_opinion、attribution、reform_target、current_package_stance、succession.項目名の形式で、不明となった項目だけを列挙する。この配列は本人・改正・継承の主要項目に限定し、other_evaluationsのunknownは各評価のassessment内で保持してunknown_fieldsへ重複列挙しない。保存検査は両方を走査し、いずれかに判断不能があればuncertain=true・evidence_sufficient=falseを要求する。uncertain/evidence_sufficientはbool、reasonは空でない文字列。

各判断はindex / is_relevant / is_opinion / attribution / main_issue / reform_target / mentioned_reform_target / current_package_stance / provisions / succession / other_succession / other_evaluations / unknown_fields / uncertain / evidence_sufficient / reason / aggregation_route / existing_stance_candidateを持つ。aggregation_routeは今回全件criteria_needed、existing_stance_candidateはnull。根拠十分は解釈の根拠を指し、事実の正しさではない。

入力には旧index・ID・本文・本文ハッシュ・旧分類版ハッシュだけを置き、旧分類値・旧回答・今回の相手の値を含めない。開始時刻、終了時刻、actor、worktree、packet/基準ハッシュを保存する。個別理由と本文は外付けの非公開領域だけに置く。保存済み値を上書きせず、相違は別の比較記録に残す。

v5の保存仕様への適合確認は、v4で独立保存した5件の値を変更せず検査する。v5を未見本文で独立分類したという意味にはしない。

新規本文確認への加算は0。5例で一致しても、現在案への支持・反対の対照例や未見標本の精度を確認したことにはならない。今回の結論だけで782件の予約・本文確認を再開しない。
