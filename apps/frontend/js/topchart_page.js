// topchart_page.js
// console.log("✅ topchart_page.js loaded");

// ===== 더미 데이터 =====
// 실제 서비스에서는 KIS API + PostgreSQL/Redis 연동 데이터로 대체 예정
const topVolumeStocks = [
  {
    rank: 1,
    name: "제영솔루텍",
    code: "049630",
    market: "KOSDAQ",
    price: 6230,
    change: 430,
    changePercent: 7.41,
    volume: 12345678,
    volumeRatio: 520, // 전일 대비 520%
  },
  {
    rank: 2,
    name: "삼성전자",
    code: "005930",
    market: "KOSPI",
    price: 82500,
    change: 2100,
    changePercent: 2.61,
    volume: 9876543,
    volumeRatio: 380,
  },
  {
    rank: 3,
    name: "엘앤에프",
    code: "066970",
    market: "KOSDAQ",
    price: 154000,
    change: -3200,
    changePercent: -2.03,
    volume: 5123456,
    volumeRatio: 340,
  },
  {
    rank: 4,
    name: "POSCO홀딩스",
    code: "005490",
    market: "KOSPI",
    price: 471500,
    change: 8500,
    changePercent: 1.84,
    volume: 3890000,
    volumeRatio: 310,
  },
  {
    rank: 5,
    name: "에코프로비엠",
    code: "247540",
    market: "KOSDAQ",
    price: 256000,
    change: 6000,
    changePercent: 2.40,
    volume: 3540000,
    volumeRatio: 295,
  },
  {
    rank: 6,
    name: "NAVER",
    code: "035420",
    market: "KOSPI",
    price: 198000,
    change: 1500,
    changePercent: 0.76,
    volume: 2980000,
    volumeRatio: 260,
  },
  {
    rank: 7,
    name: "카카오",
    code: "035720",
    market: "KOSPI",
    price: 61200,
    change: -700,
    changePercent: -1.13,
    volume: 2740000,
    volumeRatio: 245,
  },
  {
    rank: 8,
    name: "셀트리온헬스케어",
    code: "091990",
    market: "KOSDAQ",
    price: 71000,
    change: 900,
    changePercent: 1.28,
    volume: 2300000,
    volumeRatio: 230,
  },
  {
    rank: 9,
    name: "현대모비스",
    code: "012330",
    market: "KOSPI",
    price: 267500,
    change: 3500,
    changePercent: 1.33,
    volume: 2100000,
    volumeRatio: 215,
  },
  {
    rank: 10,
    name: "JYP Ent.",
    code: "035900",
    market: "KOSDAQ",
    price: 72000,
    change: 1800,
    changePercent: 2.56,
    volume: 1850000,
    volumeRatio: 205,
  },
];

// ===== 렌더링 함수 =====

function renderTopVolumeTable(stocks, marketFilter = "ALL") {
  const tbody = document.getElementById("volume-table-body");
  if (!tbody) return;

  // 1) 시장 필터 적용
  let filtered = stocks.filter((s) => {
    if (marketFilter === "ALL") return true;
    return s.market === marketFilter;
  });

  // 2) 전일 대비 거래량 비율(volumeRatio) 기준 내림차순 정렬
  filtered = filtered.sort((a, b) => b.volumeRatio - a.volumeRatio);

  // 3) 테이블 비우고 다시 렌더링
  tbody.innerHTML = "";

  filtered.forEach((s) => {
    const tr = document.createElement("tr");

    // 데이터 속성
    tr.dataset.code = s.code;
    tr.dataset.name = s.name;
    tr.dataset.market = s.market;

    // 🔗 행 전체 클릭 시 대시보드 페이지로 이동
    tr.addEventListener("click", () => {
      const code = encodeURIComponent(s.code);
      window.location.href = `./dashboard.html?code=${code}`;
    });

    // ✅ 순위: 데이터에 들어있는 s.rank 그대로 사용
    const rankTd = document.createElement("td");
    const rankSpan = document.createElement("span");
    rankSpan.className =
      "rank-badge " + (s.rank <= 3 ? "rank-badge-top3" : "");
    rankSpan.textContent = s.rank;
    rankTd.appendChild(rankSpan);

    // 종목명 / 코드
    const nameTd = document.createElement("td");
    nameTd.innerHTML = `
      <span class="stock-name">${s.name}</span>
      <span class="stock-code">${s.code} · ${s.market}</span>
    `;

    // 현재가
    const priceTd = document.createElement("td");
    priceTd.className = "price-cell";
    priceTd.textContent = s.price.toLocaleString();

    // 등락률
    const changeTd = document.createElement("td");
    const isUp = s.changePercent >= 0;
    const cls = isUp ? "change-positive" : "change-negative";
    const sign = isUp ? "+" : "-";
    changeTd.className = cls;
    changeTd.textContent = `${sign}${Math.abs(s.changePercent).toFixed(2)}%`;

    // 거래량 + 비율
    const volumeTd = document.createElement("td");
    volumeTd.className = "volume-cell";
    volumeTd.innerHTML = `
      ${s.volume.toLocaleString()}
      <div class="volume-ratio">${s.volumeRatio.toLocaleString()}%</div>
    `;

    tr.appendChild(rankTd);
    tr.appendChild(nameTd);
    tr.appendChild(priceTd);
    tr.appendChild(changeTd);
    tr.appendChild(volumeTd);

    tbody.appendChild(tr);
  });
}

function setupFilters() {
  const marketButtons = document.querySelectorAll(".filter-pill[data-market]");

  marketButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      // 시장 버튼들 active 토글
      marketButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const marketFilter = btn.getAttribute("data-market") || "ALL";
      renderTopVolumeTable(topVolumeStocks, marketFilter);
    });
  });
}


// 기준 시각 더미 세팅 (그냥 오늘 날짜 문자열 정도)
function updateAsOfLabel() {
  const el = document.getElementById("as-of-label");
  if (!el) return;

  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  const hh = String(now.getHours()).padStart(2, "0");
  const mi = String(now.getMinutes()).padStart(2, "0");

  el.textContent = `기준: ${yyyy}-${mm}-${dd} ${hh}:${mi}`;
}

// ===== 초기화 =====
document.addEventListener("DOMContentLoaded", () => {
  updateAsOfLabel();
  renderTopVolumeTable(topVolumeStocks, "ALL");
  setupFilters();
});
