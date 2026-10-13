// 自転車の青切符 冒頭試作の操作。文言は持たず、生成されたHTMLの data 属性だけを読む。
// JavaScript が無くても、16歳以上の答えと反則金10例は最初から表示されている。
(function () {
  "use strict";
  var root = document.querySelector(".bop");
  if (!root) return;

  var ageButtons = Array.prototype.slice.call(root.querySelectorAll("[data-bop-age]"));
  var ageTitle = root.querySelector("[data-bop-age-title]");
  var ageBody = root.querySelector("[data-bop-age-body]");
  ageButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      ageButtons.forEach(function (b) { b.setAttribute("aria-pressed", b === button ? "true" : "false"); });
      ageTitle.textContent = button.getAttribute("data-title");
      ageBody.textContent = button.getAttribute("data-body");
    });
  });

  var search = root.querySelector("#bop-fine-search");
  var fines = Array.prototype.slice.call(root.querySelectorAll(".bop-fine"));
  var feeButtons = Array.prototype.slice.call(root.querySelectorAll("[data-bop-fee]"));
  var count = root.querySelector("[data-bop-fine-count]");
  var empty = root.querySelector("[data-bop-fine-empty]");
  var activeFee = "all";
  var normalize = function (v) { return v.toLocaleLowerCase("ja-JP").replace(/[\s,，、円]/g, ""); };
  var update = function () {
    var term = normalize(search.value);
    var visible = 0;
    fines.forEach(function (item) {
      var feeOk = activeFee === "all" || item.getAttribute("data-bop-amount") === activeFee;
      var hay = normalize(item.getAttribute("data-bop-search") + item.textContent);
      var show = feeOk && (!term || hay.indexOf(term) !== -1);
      item.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = visible + "件を表示中（主な例 " + fines.length + "件）";
    empty.hidden = visible !== 0;
  };
  if (search) search.addEventListener("input", update);
  feeButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      activeFee = button.getAttribute("data-bop-fee");
      feeButtons.forEach(function (b) { b.setAttribute("aria-pressed", b === button ? "true" : "false"); });
      update();
    });
  });
})();
