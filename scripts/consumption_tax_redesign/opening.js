/* 消費税減税 冒頭試作のレシート（正本。scripts/consumption_tax_opening.py が試作フォルダーへ写す）。
   税率と税込額は持たない。生成時に埋め込んだ #cto-calc-data の文字を差し替えるだけ。
   JSが動かないときは、全品目の表（data-cto-static）がそのまま見える。 */
(function () {
  'use strict';
  var root = document.querySelector('[data-cto-calc]');
  var source = document.getElementById('cto-calc-data');
  if (!root || !source) return;
  var data;
  try { data = JSON.parse(source.textContent); } catch (_) { return; }
  var keys = root.querySelector('[role="tablist"]');
  var receipt = document.getElementById('cto-receipt');
  var table = root.querySelector('[data-cto-static]');
  var tabs = Array.prototype.slice.call(root.querySelectorAll('[data-cto-item]'));
  if (!keys || !receipt || !tabs.length) return;

  function fill(name, value) {
    var node = receipt.querySelector('[data-cto="' + name + '"]');
    if (node) node.textContent = value;
  }

  function select(index, focus) {
    var tab = tabs[index];
    var item = data[tab.getAttribute('data-cto-item')];
    if (!item) return;
    tabs.forEach(function (other, i) {
      other.setAttribute('aria-selected', i === index ? 'true' : 'false');
      other.tabIndex = i === index ? 0 : -1;
    });
    receipt.setAttribute('aria-labelledby', tab.id);
    fill('before_rate', item.before_rate + '%');
    fill('after_rate', item.after_rate + '%');
    fill('before_name', item.before_name);
    fill('after_name', item.after_name);
    fill('before_price', item.before_price);
    fill('after_price', item.after_price);
    fill('delta', item.delta);
    fill('note', item.note);
    receipt.classList.toggle('is-down', !!item.after_special);
    if (focus) tab.focus();
  }

  tabs.forEach(function (tab, index) {
    tab.addEventListener('click', function () { select(index, false); });
    tab.addEventListener('keydown', function (event) {
      var next = index;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      else return;
      event.preventDefault();
      select(next, true);
    });
  });

  keys.hidden = false;
  receipt.hidden = false;
  if (table) table.hidden = true;
  select(0, false);
})();
