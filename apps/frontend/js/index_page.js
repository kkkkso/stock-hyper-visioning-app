// index_page.js
console.log("✅ index_page.js loaded");

document.addEventListener("DOMContentLoaded", () => {
  const topchartBtn = document.getElementById("btn-topchart");
  const comingSoonBtn = document.getElementById("btn-comingsoon");

  if (topchartBtn) {
    topchartBtn.addEventListener("click", () => {
      // 거래량 상승 TOP 차트 페이지로 이동
      window.location.href = "./topchart.html";
    });
  }

  if (comingSoonBtn) {
    comingSoonBtn.addEventListener("click", () => {
      alert("추가 예정 기능입니다. 곧 더 많은 분석이 추가될 예정이에요 🚧");
    });
  }
});
