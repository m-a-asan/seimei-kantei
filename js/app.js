(function () {
  "use strict";

  const form = document.getElementById("name-form");
  const seiInput = document.getElementById("input-sei");
  const meiInput = document.getElementById("input-mei");
  const errorBox = document.getElementById("form-error");
  const resultSection = document.getElementById("result");
  const introSection = document.getElementById("intro");

  const KANA_RE = /[ぁ-んァ-ヶーｦ-ﾟ]/;

  function splitChars(str) {
    return Array.from(str.trim());
  }

  function validateAndGetStrokes(chars) {
    const unknown = [];
    const strokes = [];
    for (let i = 0; i < chars.length; i++) {
      const c = chars[i];
      if (c === "々" && i > 0 && strokes[i - 1] !== null) {
        // 踊り字は直前の漢字の繰り返し（佐々木 → 佐の7画を引き継ぐ）
        strokes.push(strokes[i - 1]);
        continue;
      }
      const n = getKanjiStrokes(c);
      if (n === null) unknown.push(c);
      strokes.push(n);
    }
    return { strokes, unknown };
  }

  function calcFortune(seiChars, meiChars) {
    const seiInfo = validateAndGetStrokes(seiChars);
    const meiInfo = validateAndGetStrokes(meiChars);
    const unknown = [...seiInfo.unknown, ...meiInfo.unknown];
    if (unknown.length > 0) {
      return { error: unknown };
    }

    const seiSum = seiInfo.strokes.reduce((a, b) => a + b, 0);
    const meiSum = meiInfo.strokes.reduce((a, b) => a + b, 0);

    const tenkaku = seiChars.length === 1 ? seiSum + 1 : seiSum;
    const chikaku = meiChars.length === 1 ? meiSum + 1 : meiSum;
    const jinkaku = seiInfo.strokes[seiInfo.strokes.length - 1] + meiInfo.strokes[0];
    const soukaku = seiSum + meiSum;
    const adjustment =
      seiChars.length === 1 && meiChars.length === 1 ? 2 : seiChars.length === 1 || meiChars.length === 1 ? 1 : 0;
    const gaikaku = soukaku - jinkaku + adjustment;

    const allStrokes = [...seiInfo.strokes, ...meiInfo.strokes];
    const parity = allStrokes.map((n) => (n % 2 === 0 ? "陰" : "陽"));
    let alternating = true;
    for (let i = 1; i < parity.length; i++) {
      if (parity[i] === parity[i - 1]) alternating = false;
    }
    const allSame = parity.every((p) => p === parity[0]);
    let inyouLabel, inyouText;
    if (allSame) {
      inyouLabel = "偏り注意";
      inyouText = `${parity[0]}${parity[0] === "陽" ? "陽" : "陰"}のみで構成されており、エネルギーが一方向に偏りやすい傾向。意識的に別の側面を取り入れるとバランスが整います。`;
    } else if (alternating) {
      inyouLabel = "陰陽調和";
      inyouText = "陰と陽が美しく交互に並ぶ、調和のとれた配列です。物事のバランスを取るのが自然と得意なタイプ。";
    } else {
      inyouLabel = "良好";
      inyouText = "陰陽ともに程よく混ざり合い、状況に応じて柔軟に対応できるバランス感覚を持っています。";
    }

    return {
      tenkaku,
      chikaku,
      jinkaku,
      gaikaku,
      soukaku,
      seiStrokes: seiInfo.strokes,
      meiStrokes: meiInfo.strokes,
      inyou: { label: inyouLabel, text: inyouText },
    };
  }

  function rankClass(rank) {
    if (rank === FORTUNE_RANK.GREAT) return "rank-great";
    if (rank === FORTUNE_RANK.GOOD) return "rank-good";
    if (rank === FORTUNE_RANK.NORMAL) return "rank-normal";
    if (rank === FORTUNE_RANK.CAUTION) return "rank-caution";
    return "rank-hard";
  }

  function renderGrid(id, label, value, sublabel) {
    const meaning = getNumberMeaning(value);
    return `
      <div class="grid-card ${rankClass(meaning.rank)}" data-grid="${id}">
        <div class="grid-card-seal">
          <span class="grid-card-label">${label}</span>
          <span class="grid-card-value">${value}</span>
        </div>
        <div class="grid-card-body">
          <div class="grid-card-sub">${sublabel}</div>
          <div class="grid-card-rank">${meaning.rank}・${meaning.title}</div>
          <p class="grid-card-text">${meaning.text}</p>
        </div>
      </div>`;
  }

  function renderStrokeBreakdown(seiChars, meiChars, fortune) {
    const cell = (ch, n) => `
      <div class="stroke-cell">
        <span class="stroke-char">${ch}</span>
        <span class="stroke-num">${n}<small>画</small></span>
      </div>`;
    const seiCells = seiChars.map((c, i) => cell(c, fortune.seiStrokes[i])).join("");
    const meiCells = meiChars.map((c, i) => cell(c, fortune.meiStrokes[i])).join("");
    return `
      <div class="stroke-row">
        ${seiCells}
        <div class="stroke-divider"></div>
        ${meiCells}
      </div>`;
  }

  function renderResult(seiChars, meiChars, fortune) {
    const sei = seiChars.join("");
    const mei = meiChars.join("");
    const jinMeaning = getNumberMeaning(fortune.jinkaku);
    const souMeaning = getNumberMeaning(fortune.soukaku);

    resultSection.innerHTML = `
      <div class="result-header">
        <p class="result-name-label">鑑定結果</p>
        <h2 class="result-name">${sei} <span class="name-space"></span> ${mei}</h2>
        ${renderStrokeBreakdown(seiChars, meiChars, fortune)}
      </div>

      <div class="grid-wrap">
        ${renderGrid("ten", "天格", fortune.tenkaku, "先祖から受け継ぐ気質・家系の土台")}
        ${renderGrid("jin", "人格", fortune.jinkaku, "生まれ持った性格・対人関係の要")}
        ${renderGrid("chi", "地格", fortune.chikaku, "幼少期〜青年期の運勢・基礎体力")}
        ${renderGrid("gai", "外格", fortune.gaikaku, "対外運・社会での立ち回り")}
        ${renderGrid("sou", "総格", fortune.soukaku, "人生全体を貫く運勢・晩年運")}
      </div>

      <div class="inyou-card">
        <h3>陰陽バランス：${fortune.inyou.label}</h3>
        <p>${fortune.inyou.text}</p>
      </div>

      <div class="summary-card">
        <h3>総合鑑定</h3>
        <p>
          あなたの核となる「人格（${fortune.jinkaku}画）」は<strong>${jinMeaning.rank}・${jinMeaning.title}</strong>。
          そして人生全体を貫く「総格（${fortune.soukaku}画）」は<strong>${souMeaning.rank}・${souMeaning.title}</strong>です。
          この二つが響き合いながら、あなたらしい人生の物語を紡いでいきます。
        </p>
      </div>

      <div class="share-row">
        <button type="button" id="btn-retry" class="btn-secondary">別の名前で調べる</button>
        <a class="btn-share" id="btn-share-x" target="_blank" rel="noopener">Xでシェア</a>
        <a class="btn-share btn-share-line" id="btn-share-line" target="_blank" rel="noopener">LINEで送る</a>
      </div>
    `;

    resultSection.hidden = false;
    introSection.hidden = true;
    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });

    document.getElementById("btn-retry").addEventListener("click", () => {
      resultSection.hidden = true;
      introSection.hidden = false;
      resultSection.innerHTML = "";
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    const shareText = encodeURIComponent(
      `私の総格は${fortune.soukaku}画「${souMeaning.title}」でした。あなたの名前の運勢は？ #姓名鑑定 #人生これから研究所`
    );
    const shareUrl = encodeURIComponent(window.location.href);
    document.getElementById("btn-share-x").href = `https://twitter.com/intent/tweet?text=${shareText}&url=${shareUrl}`;
    document.getElementById("btn-share-line").href = `https://social-plugins.line.me/lineit/share?url=${shareUrl}`;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    errorBox.hidden = true;
    errorBox.textContent = "";

    const seiRaw = seiInput.value.trim();
    const meiRaw = meiInput.value.trim();

    if (!seiRaw || !meiRaw) {
      errorBox.textContent = "姓と名の両方を漢字で入力してください。";
      errorBox.hidden = false;
      return;
    }
    if (KANA_RE.test(seiRaw) || KANA_RE.test(meiRaw)) {
      errorBox.textContent = "姓名判断は漢字の画数をもとに鑑定するため、ひらがな・カタカナには対応していません。漢字のみで入力してください。";
      errorBox.hidden = false;
      return;
    }

    const seiChars = splitChars(seiRaw);
    const meiChars = splitChars(meiRaw);
    const fortune = calcFortune(seiChars, meiChars);

    if (fortune.error) {
      errorBox.textContent = `申し訳ございません。「${fortune.error.join("」「")}」は画数辞書に見つかりませんでした。漢字のみで、正しい表記かご確認のうえお試しください。`;
      errorBox.hidden = false;
      return;
    }

    renderResult(seiChars, meiChars, fortune);
  });
})();
