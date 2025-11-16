// ===== 더미 데이터 =====
console.log("✅ app.js loaded");

const stockInfo = {
  name: "제영솔루텍",
  code: "049630",
  market: "KOSDAQ",
  sector: "반도체/장비",
  currentPrice: 6230,
  change: 430,
  changePercent: 7.41,
  open: 5800,
  prevClose: 5800,
  high: 6450,
  low: 5700,
  volume: 12345678,
  tradingValue: 98765,
  high52w: 7800,
  low52w: 3200,
};

const investorBars = [
  { type: "개인", value: 2293, isPositive: true },
  { type: "외국인", value: -1883, isPositive: false },
  { type: "기관", value: -4080, isPositive: false },
];

// 현재 종목이 속한 섹터에 대한 요약 정보 (섹터 평균 등락률)
const sectorSummary = {
  sectorChange: 3.45, // 섹터 평균 등락률 (%)
};

const newsItems = [
  {
    id: 1,
    title: "제영솔루텍, 3분기 실적 예상치 상회...영업이익 15% 증가",
    source: "한국경제",
    time: "2시간 전",
  },
  {
    id: 2,
    title: "반도체 장비 수요 급증, 관련주 강세 지속 전망",
    source: "매일경제",
    time: "4시간 전",
  },
  {
    id: 3,
    title: "외국인, 코스닥 IT·부품주 순매수 확대",
    source: "연합뉴스",
    time: "6시간 전",
  },
];

const vitalityData = {
  overall: 78,
  volumeScore: 85,
  priceVolatility: 72,
  marketInterest: 81,
};

// 기간별 차트용 더미
function getChartData(period) {
  if (period === "1D") {
    return {
      labels: ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"],
      prices: [5800, 5950, 6020, 6100, 6200, 6300, 6230],
    };
  }
  if (period === "1W") {
    return {
      labels: ["월", "화", "수", "목", "금"],
      prices: [5420, 5600, 5750, 5900, 6230],
    };
  }
  if (period === "1M") {
    return {
      labels: ["1주차", "2주차", "3주차", "4주차"],
      prices: [5100, 5400, 5800, 6230],
    };
  }
  if (period === "3M") {
    return {
      labels: ["-3M", "-2M", "-1M", "현재"],
      prices: [4300, 4800, 5400, 6230],
    };
  }
  // 1Y
  return {
    labels: ["-1Y", "-9M", "-6M", "-3M", "현재"],
    prices: [3200, 3800, 4500, 5200, 6230],
  };
}

// ===== 렌더링 함수 =====

function renderStockHeader(info) {
  document.getElementById("stock-sector-badge").textContent = info.sector;
  document.getElementById("stock-name-main").textContent = info.name;
  document.getElementById("stock-code-main").textContent =
    `${info.code} · ${info.market}`;
  document.getElementById("stock-price-main").textContent =
    info.currentPrice.toLocaleString();

  const changeEl = document.getElementById("stock-change-main");
  const sign = info.change >= 0 ? "+" : "-";
  const cls = info.change >= 0 ? "text-danger" : "text-primary";
  changeEl.classList.add(cls);
  changeEl.textContent =
    `${sign}${Math.abs(info.change).toLocaleString()} (${sign}${Math.abs(info.changePercent)}%)`;
}

function renderMetrics(info) {
  document.getElementById("metric-open").textContent =
    info.open.toLocaleString();
  document.getElementById("metric-prev-close").textContent =
    info.prevClose.toLocaleString();
  document.getElementById("metric-volume").textContent =
    info.volume.toLocaleString();
  document.getElementById("metric-trading-value").textContent =
    info.tradingValue.toLocaleString();

  document.getElementById("metric-high").textContent =
    info.high.toLocaleString();
  document.getElementById("metric-low").textContent =
    info.low.toLocaleString();
  document.getElementById("metric-52w").textContent =
    `${info.high52w.toLocaleString()} / ${info.low52w.toLocaleString()}`;
}

function renderInvestorBars(data) {
  const container = document.getElementById("investor-bars");
  container.innerHTML = "";
  const maxAbs = Math.max(...data.map((d) => Math.abs(d.value)));

  data.forEach((trend) => {
    const row = document.createElement("div");
    row.className = "investor-row";

    const label = document.createElement("div");
    label.className = "investor-label";
    label.textContent = trend.type;

    const barArea = document.createElement("div");
    barArea.className = "investor-bar-area";

    const halfLeft = document.createElement("div");
    halfLeft.className = "investor-half investor-half-left";

    const axis = document.createElement("div");
    axis.className = "investor-axis";

    const halfRight = document.createElement("div");
    halfRight.className = "investor-half investor-half-right";

    const percentage = (Math.abs(trend.value) / maxAbs) * 50; // 한쪽 최대 50%

    // 음수 → 왼쪽 파란색
    if (!trend.isPositive) {
      const barNeg = document.createElement("div");
      barNeg.className = "investor-bar-fill negative";
      barNeg.style.width = `${percentage}%`;
      halfLeft.appendChild(barNeg);
    }

    // 양수 → 오른쪽 빨간색
    if (trend.isPositive) {
      const barPos = document.createElement("div");
      barPos.className = "investor-bar-fill positive";
      barPos.style.width = `${percentage}%`;
      halfRight.appendChild(barPos);
    }

    barArea.appendChild(halfLeft);
    barArea.appendChild(axis);
    barArea.appendChild(halfRight);

    const value = document.createElement("div");
    value.className =
      "investor-value " +
      (trend.isPositive ? "text-danger" : "text-primary");
    value.textContent =
      (trend.isPositive ? "+" : "") + trend.value.toLocaleString();

    row.appendChild(label);
    row.appendChild(barArea);
    row.appendChild(value);

    container.appendChild(row);
  });
}

// 🔵 해당 섹터 등락률 렌더링
function renderSectorSummary(info, summary) {
  const container = document.getElementById("sector-summary");
  const sectorChange = summary.sectorChange;
  const stockChange = info.changePercent;

  const sectorSign = sectorChange >= 0 ? "+" : "-";
  const sectorColorClass = sectorChange >= 0 ? "text-danger" : "text-primary";
  const sectorArrow = sectorChange >= 0 ? "↗" : "↘";

  const stockSign = stockChange >= 0 ? "+" : "-";
  const stockColorClass = stockChange >= 0 ? "text-danger" : "text-primary";

  container.innerHTML = `
    <div class="sector-summary-card">
      <div class="sector-summary-header">
        <div>
          <div class="sector-summary-name">${info.sector}</div>
          <div class="sector-summary-tag">섹터 평균</div>
        </div>
        <div class="sector-summary-sector-change ${sectorColorClass}">
          <span>${sectorArrow}</span>
          <span>${sectorSign}${Math.abs(sectorChange).toFixed(2)}%</span>
        </div>
      </div>
      <hr class="sector-summary-divider">
      <div class="d-flex justify-content-between align-items-center">
        <span class="sector-summary-tag">종목 등락률</span>
        <span class="sector-summary-stock-change ${stockColorClass}">
          ${stockSign}${Math.abs(stockChange).toFixed(2)}%
        </span>
      </div>
    </div>
  `;
}

function renderNews(items) {
  const container = document.getElementById("news-list");
  container.innerHTML = "";
  items.forEach((n) => {
    const div = document.createElement("div");
    div.className = "news-item";
    div.innerHTML = `
      <div>
        <div class="font-weight-bold mb-1">${n.title}</div>
        <div class="news-meta">
          <span>${n.source}</span>
          <span> · </span>
          <span>${n.time}</span>
        </div>
      </div>
    `;
    container.appendChild(div);
  });
}

function renderVitality(v) {
  const badge = document.getElementById("vitality-score-badge");
  let level = "보통";
  if (v.overall >= 80) level = "높음";
  if (v.overall < 50) level = "낮음";
  badge.textContent = `${v.overall}점 · ${level}`;

  document.getElementById("vitality-volume-label").textContent =
    `${v.volumeScore}점`;
  document.getElementById("vitality-volatility-label").textContent =
    `${v.priceVolatility}점`;
  document.getElementById("vitality-interest-label").textContent =
    `${v.marketInterest}점`;

  document.getElementById("vitality-volume-bar").style.width =
    `${v.volumeScore}%`;
  document.getElementById("vitality-volatility-bar").style.width =
    `${v.priceVolatility}%`;
  document.getElementById("vitality-interest-bar").style.width =
    `${v.marketInterest}%`;
}

// ===== Chart.js =====

let priceChart = null;

function renderChart(period) {
  const ctx = document.getElementById("priceChart").getContext("2d");
  const data = getChartData(period);

  if (priceChart) {
    priceChart.destroy();
  }

  priceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "종가",
          data: data.prices,
          fill: false,
          borderWidth: 2,
        },
      ],
    },
    options: {
      legend: { display: false },
      scales: {
        xAxes: [{ gridLines: { display: false } }],
        yAxes: [
          {
            ticks: {
              callback: (value) => value.toLocaleString(),
            },
          },
        ],
      },
      tooltips: {
        callbacks: {
          label: (tooltipItem) =>
            tooltipItem.yLabel.toLocaleString() + "원",
        },
      },
    },
  });
}

function setupPeriodButtons() {
  const buttons = document.querySelectorAll(".period-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const period = btn.getAttribute("data-period");
      renderChart(period);
    });
  });
}

// ===== 초기화 =====

document.addEventListener("DOMContentLoaded", () => {
  renderStockHeader(stockInfo);
  renderMetrics(stockInfo);
  renderInvestorBars(investorBars);
  renderSectorSummary(stockInfo, sectorSummary);
  renderNews(newsItems);
  renderVitality(vitalityData);
  renderChart("1D");
  setupPeriodButtons();
});
