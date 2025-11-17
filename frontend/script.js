const apiBaseInput = document.getElementById("apiBase");
const interestInput = document.getElementById("interestInput");
const recommendBtn = document.getElementById("recommendBtn");
const itemsGrid = document.getElementById("itemsGrid");
const recommendationsGrid = document.getElementById("recommendationsGrid");
const cardTemplate = document.getElementById("cardTemplate");
const likedCount = document.getElementById("likedCount");

let likedIds = new Set();
let items = [];

function apiUrl(path) {
  return `${apiBaseInput.value}${path}`;
}

function updateLikedCount() {
  likedCount.textContent = `${likedIds.size} liked`;
}

function renderCard(item, { showScore = false } = {}) {
  const clone = cardTemplate.content.cloneNode(true);
  const article = clone.querySelector(".card");
  article.dataset.id = item.id;
  clone.querySelector(".card__title").textContent = item.title;
  clone.querySelector(".card__category").textContent = item.category;
  clone.querySelector(".card__snippet").textContent = item.snippet;

  const likeBtn = clone.querySelector(".like");
  if (likedIds.has(item.id)) {
    likeBtn.classList.add("is-active");
  }

  likeBtn.addEventListener("click", () => {
    if (likedIds.has(item.id)) {
      likedIds.delete(item.id);
      likeBtn.classList.remove("is-active");
    } else {
      likedIds.add(item.id);
      likeBtn.classList.add("is-active");
    }
    updateLikedCount();
  });

  const scoreLabel = clone.querySelector(".score");
  if (showScore && typeof item.score === "number") {
    scoreLabel.textContent = `${item.score.toFixed(3)} sim.`;
  } else {
    scoreLabel.textContent = "";
  }

  return clone;
}

async function loadItems() {
  itemsGrid.innerHTML = "<p>Loading feed...</p>";
  try {
    const res = await fetch(apiUrl("/items?limit=50"));
    const data = await res.json();
    items = data;
    itemsGrid.innerHTML = "";
    data.forEach((item) => itemsGrid.appendChild(renderCard(item)));
  } catch (error) {
    console.error(error);
    itemsGrid.innerHTML = `<p class="error">Failed to load items. Check your API URL.</p>`;
  }
}

async function loadRecommendations() {
  recommendationsGrid.innerHTML = "<p>Loading recommendations...</p>";
  try {
    const payload = {
      query: interestInput.value,
      liked_ids: Array.from(likedIds),
      limit: 12,
    };
    const res = await fetch(apiUrl("/recommendations"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    recommendationsGrid.innerHTML = "";
    data.forEach((item) => recommendationsGrid.appendChild(renderCard(item, { showScore: true })));
  } catch (error) {
    console.error(error);
    recommendationsGrid.innerHTML = `<p class="error">Failed to load recommendations.</p>`;
  }
}

recommendBtn.addEventListener("click", loadRecommendations);

// Initial load
loadItems();
