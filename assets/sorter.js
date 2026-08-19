/* ============================================================
   共用分類練習元件 — 把一組項目歸到正確的類別
   用法:
     <div class="sorter" data-buckets="結帳|倉儲|財務|三邊都有">
       <div class="sorter-item" data-answer="0" data-why="為什麼是這個">優惠券折抵金額</div>
       ...
     </div>
   data-buckets 用 | 分隔;data-answer 是正確 bucket 的 index(從 0 起算)。
   每一項作答後立刻給回饋並顯示理由 —— 回饋迴圈要緊,錯的當下就要知道為什麼。
   ============================================================ */

(function () {
  'use strict';

  function initSorter(sorter) {
    var buckets = (sorter.dataset.buckets || '').split('|');
    var items = Array.prototype.slice.call(sorter.querySelectorAll('.sorter-item'));
    var total = items.length;
    var answered = 0;
    var right = 0;

    var score = document.createElement('div');
    score.className = 'sorter-score';
    score.textContent = '共 ' + total + ' 題,尚未作答';
    sorter.appendChild(score);

    items.forEach(function (item) {
      var correct = parseInt(item.dataset.answer, 10);
      var why = item.dataset.why || '';

      // 原本的文字內容變成標題
      var label = document.createElement('div');
      label.className = 'sorter-label';
      label.textContent = item.textContent.trim();
      item.textContent = '';
      item.appendChild(label);

      var btns = document.createElement('div');
      btns.className = 'sorter-btns';
      item.appendChild(btns);

      var whyEl = document.createElement('div');
      whyEl.className = 'sorter-why';
      whyEl.textContent = why;
      item.appendChild(whyEl);

      var made = [];
      buckets.forEach(function (name, i) {
        var b = document.createElement('button');
        b.className = 'sorter-btn';
        b.textContent = name;
        b.addEventListener('click', function () {
          if (item.dataset.done === 'true') return;
          item.dataset.done = 'true';
          answered++;
          if (i === correct) right++;

          made.forEach(function (x, j) {
            x.disabled = true;
            if (j === correct) x.classList.add('is-right');
          });
          if (i !== correct) b.classList.add('is-wrong');
          whyEl.classList.add('show');

          score.textContent = answered < total
            ? '已作答 ' + answered + '/' + total + ',答對 ' + right
            : '完成 —— ' + total + ' 題答對 ' + right + ' 題';
        });
        made.push(b);
        btns.appendChild(b);
      });
    });
  }

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    document.querySelectorAll('.sorter').forEach(initSorter);
  });
})();
