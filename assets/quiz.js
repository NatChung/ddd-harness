/* ============================================================
   共用測驗元件 — 所有 lessons 共用
   用法:
     <div class="quiz" data-answer="1">
       <p class="quiz-q">問題文字</p>
       <div class="quiz-opts">
         <button class="quiz-opt">選項 A</button>
         <button class="quiz-opt">選項 B</button>
       </div>
       <div class="quiz-fb" data-right="答對時的回饋" data-wrong="答錯時的回饋"></div>
     </div>
   data-answer 是正確選項的 index(從 0 起算)。
   回饋一律兩則都顯示解釋,答錯不只說「錯了」——錯誤本身要能教東西。
   ============================================================ */

(function () {
  'use strict';

  function initQuiz(quiz) {
    var correct = parseInt(quiz.dataset.answer, 10);
    var opts = Array.prototype.slice.call(quiz.querySelectorAll('.quiz-opt'));
    var fb = quiz.querySelector('.quiz-fb');

    opts.forEach(function (btn, i) {
      btn.addEventListener('click', function () {
        if (quiz.dataset.done === 'true') return;
        quiz.dataset.done = 'true';

        opts.forEach(function (b, j) {
          b.disabled = true;
          if (j === correct) b.classList.add('is-right');
        });
        if (i !== correct) btn.classList.add('is-wrong');

        if (fb) {
          var msg = i === correct
            ? '<b>答對。</b> ' + (fb.dataset.right || '')
            : '<b>不是這個。</b> ' + (fb.dataset.wrong || '');
          fb.innerHTML = msg;
          fb.classList.add('show');
        }
      });
    });
  }

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    document.querySelectorAll('.quiz').forEach(initQuiz);
  });
})();
