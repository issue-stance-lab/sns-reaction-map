(function () {
  "use strict";

  var root = document.getElementById("bike-search-entry");
  if (!root) return;

  var ageAnswers = {
    under13: {
      title: "13歳未満は青切符制度の対象外です",
      body: "歩道を通行できます。歩道では歩行者を優先し、車道寄りを徐行してください。"
    },
    "13to15": {
      title: "13〜15歳は青切符制度の対象外です",
      body: "交通ルールがなくなるわけではありません。歩道通行の年齢例外は13歳未満で、この区分とは異なります。"
    },
    "16plus": {
      title: "16歳以上は制度の対象です",
      body: "一定の反則行為で検挙された場合に手続きの対象となります。通常は指導警告が基本です。免許の有無は対象年齢に関係しません。"
    }
  };
  var ageButtons = Array.prototype.slice.call(root.querySelectorAll("[data-bse-age]"));
  var ageTitle = root.querySelector("#bike-age-answer-title");
  var ageBody = root.querySelector("#bike-age-answer-body");

  ageButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      var answer = ageAnswers[button.getAttribute("data-bse-age")];
      if (!answer) return;
      ageButtons.forEach(function (item) {
        item.setAttribute("aria-pressed", item === button ? "true" : "false");
      });
      ageTitle.textContent = answer.title;
      ageBody.textContent = answer.body;
    });
  });

  var search = root.querySelector("#bike-fine-search");
  var fineCards = Array.prototype.slice.call(root.querySelectorAll(".bike-fine-item"));
  var feeButtons = Array.prototype.slice.call(root.querySelectorAll("[data-bse-fee]"));
  var resultCount = root.querySelector("#bike-fine-count");
  var emptyState = root.querySelector("#bike-fine-empty");
  var activeFee = "all";
  var normalize = function (value) {
    return value.toLocaleLowerCase("ja-JP").replace(/[\s,，、円]/g, "");
  };
  var updateFineList = function () {
    var term = normalize(search.value);
    var visible = 0;
    fineCards.forEach(function (card) {
      var matchesFee = activeFee === "all" || card.getAttribute("data-bse-amount") === activeFee;
      var haystack = normalize(card.getAttribute("data-bse-search") + " " + card.querySelector("h4").textContent + " " + card.querySelector("strong").textContent);
      var matchesTerm = !term || haystack.indexOf(term) !== -1;
      var show = matchesFee && matchesTerm;
      card.hidden = !show;
      if (show) visible += 1;
    });
    resultCount.textContent = visible + "件を表示中（主な例 " + fineCards.length + "件）";
    emptyState.hidden = visible !== 0;
  };

  search.addEventListener("input", updateFineList);
  feeButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      activeFee = button.getAttribute("data-bse-fee");
      feeButtons.forEach(function (item) {
        item.setAttribute("aria-pressed", item === button ? "true" : "false");
      });
      updateFineList();
    });
  });

  root.querySelectorAll("[data-bse-open]").forEach(function (button) {
    button.addEventListener("click", function () {
      var target = root.querySelector("#" + button.getAttribute("data-bse-open"));
      if (!target) return;
      target.open = true;
      var summary = target.querySelector("summary");
      var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      target.scrollIntoView({ block: "center", behavior: reduceMotion ? "auto" : "smooth" });
      if (summary) summary.focus({ preventScroll: true });
    });
  });
})();
