// st が閲覧状態の唯一の保持場所。投票・クイズ・収集比較の状態には触れない。
function taxState(){
  const stance = D.stances.find(s => s.key === st.mode);
  return Object.freeze({
    stanceId: stance ? stance.id : "all",
    issueId: st.landed === null ? null : issues[st.landed].id
  });
}
let taxLastState = "";
function taxPublish(){
  const state = taxState();
  document.querySelectorAll("#modes [data-m]").forEach(b => {
    b.setAttribute("aria-pressed", String(b.dataset.m === st.mode));
  });
  document.dispatchEvent(new CustomEvent("tax-map:render", {detail: state}));
  const key = JSON.stringify(state);
  if (key === taxLastState) return;
  taxLastState = key;
  document.dispatchEvent(new CustomEvent("tax-map:change", {detail: state}));
}
const taxOriginalLand = land;
land = function(i){
  if (!Number.isInteger(i) || !issues[i]) return;
  taxOriginalLand(i);
  taxPublish();
};
const taxOriginalMorph = morphTo;
morphTo = function(mode){
  if (!modeById[mode]) return;
  taxOriginalMorph(mode);
  taxPublish();
};
const taxOriginalOrbit = orbit;
orbit = function(){ taxOriginalOrbit(); taxPublish(); };
window.ConsumptionTaxMap = Object.freeze({
  getState: taxState,
  selectIssue: function(id){
    if (id === null) { orbit(); return true; }
    if (!Object.prototype.hasOwnProperty.call(idIndex, id)) return false;
    land(idIndex[id]);
    return true;
  },
  selectStance: function(id){
    const stance = D.stances.find(s => s.id === id);
    if (id !== "all" && !stance) return false;
    morphTo(id === "all" ? "all" : stance.key);
    return true;
  }
});
