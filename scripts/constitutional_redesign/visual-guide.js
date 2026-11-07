(() => {
  const guide = document.querySelector(".cav");
  if (!guide) return;
  const nav = guide.querySelector(".cav-nav");
  const search = guide.querySelector(".cav-search");
  const input = search.querySelector("input");
  const modes = [...nav.querySelectorAll("[data-cav-mode]")];
  const links = [...nav.querySelectorAll("li[data-kind]")];
  const mobile = matchMedia("(max-width: 820px)");
  let mode = "all";
  if (mobile.matches) nav.open = false;

  function renderIndex() {
    const query = input.value.normalize("NFKC").trim().toLowerCase();
    search.hidden = mode !== "search";
    for (const item of links) {
      const kind = item.dataset.kind;
      item.hidden = mode === "all" ? kind === "reason"
        : mode === "visual" ? !["diagram", "table", "photo"].includes(kind)
        : !query || !item.textContent.normalize("NFKC").toLowerCase().includes(query);
    }
    nav.querySelector(".cav-empty").hidden = mode !== "search" || !query || links.some(item => !item.hidden);
  }
  for (const button of modes) button.addEventListener("click", () => {
    mode = button.dataset.cavMode;
    for (const control of modes) control.setAttribute("aria-pressed", String(control === button));
    renderIndex();
    if (mode === "search") input.focus();
  });
  input.addEventListener("input", renderIndex);

  guide.addEventListener("click", event => {
    const link = event.target.closest("a");
    if (!link) return;
    if (nav.contains(link) && mobile.matches) nav.open = false;
    if (typeof window.gtag === "function") {
      window.gtag("event", "constitutional_guide_click", {
        section_id: link.hash.slice(1) || link.closest("[id]")?.id || "photo",
        entry: nav.contains(link) ? mode : "body"
      });
    }
  });
  const sections = [...guide.querySelectorAll(".cav-content > [data-readpoint]")];
  const navLinks = new Map(links.map(item => [item.firstElementChild.hash, item.firstElementChild]));
  let active;
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      active?.removeAttribute("aria-current");
      active = navLinks.get("#" + entry.target.id);
      active?.setAttribute("aria-current", "location");
    }
  }, {rootMargin: "0px 0px -70% 0px"});
  for (const section of sections) observer.observe(section);

  const filters = [...guide.querySelectorAll(".comparison-tools [data-filter]")];
  for (const button of filters) button.addEventListener("click", () => {
    for (const option of filters) option.setAttribute("aria-pressed", String(option === button));
    for (const row of guide.querySelectorAll(".compare-table tr[data-topic]")) {
      row.hidden = button.dataset.filter !== "all" && row.dataset.topic !== button.dataset.filter;
    }
  });

  const fields = ["yes", "no", "invalid"].map(key => guide.querySelector("#vote-" + key));
  const result = guide.querySelector("#cav-vote-result");
  function renderVote() {
    const valid = fields.every(field => field.validity.valid && field.value !== "");
    const [yes, no, invalid] = valid ? fields.map(field => field.valueAsNumber) : [0, 0, 0];
    const total = yes + no;
    for (const [key, label, value] of [["yes", "賛成", yes], ["no", "反対", no]]) {
      const bar = guide.querySelector("#diagram-" + key);
      bar.style.flex = String(total ? value : 1);
      bar.textContent = label + " " + value.toLocaleString("ja-JP");
    }
    guide.querySelector("#diagram-invalid").textContent = invalid.toLocaleString("ja-JP") + "票";
    guide.querySelector("#ballot-bars").setAttribute("aria-label", `賛成${yes}票、反対${no}票`);
    if (!valid) result.textContent = "票数は0以上の整数で入力してください。";
    else if (!total) result.textContent = "賛成票と反対票が0票のため、計算できません。";
    else result.textContent = `賛成は約${(100 * yes / total).toFixed(1)}％。` +
      (yes > no ? "承認条件を満たします。" : "承認条件を満たしません。");
  }
  for (const field of fields) field.addEventListener("input", renderVote);
  renderVote();
})();
