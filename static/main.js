/* Allergen filter + pretty popup details
   -------------------------------------------------------------- */

const API = "/api";                        // works locally & on Render
const $  = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

/* ---------- 1.  Populate allergen check-boxes --------------- */
async function init() {
  try {
    const allergens = await (await fetch(`${API}/allergens`)).json();
    $("#allergenCheckboxes").innerHTML = allergens
      .map(
        (a) => `
      <div class="form-check col">
        <input class="form-check-input" type="checkbox" value="${a}" id="chk-${a}">
        <label class="form-check-label" for="chk-${a}">${a}</label>
      </div>`
      )
      .join("");
  } catch (err) {
    console.error(err);
    $("#allergenCheckboxes").innerHTML =
      '<p class="text-danger">Error loading allergens.</p>';
  }
}

/* ---------- 2.  Helpers ------------------------------------- */
const selectedAllergens = () =>
  $$("#allergenCheckboxes input:checked").map((i) => i.value);

/* ---------- 3.  Search + list rendering --------------------- */
async function search() {
  const q       = $("#searchBox").value.trim();
  const exclude = selectedAllergens();

  const p = new URLSearchParams();
  exclude.forEach((e) => p.append("exclude", e));
  if (q) p.append("q", q);
  p.append("limit", 30);

  const data = await (await fetch(`${API}/recipes?${p}`)).json();
  renderResults(data);
}

function renderResults(recipes) {
  const tgt = $("#results");
  if (!recipes.length) {
    tgt.innerHTML = '<p class="text-muted"><em>No recipes found.</em></p>';
    return;
  }

  tgt.innerHTML = recipes
    .map(
      (r) => `
      <div class="col-12 col-md-6 col-lg-4 mb-3">
        <div class="card shadow-sm h-100">
          <div class="card-body d-flex flex-column">
            <h5 class="card-title mb-2">${r.title}</h5>
            <p class="card-text small flex-grow-1">
              <strong>Allergens:</strong>
              ${
                r.allergens.length
                  ? r.allergens.join(", ")
                  : "<span class='text-success'>None 🎉</span>"
              }
            </p>

            <button class="btn btn-outline-primary btn-sm mt-auto btn-details"
                    data-id="${r.id}">
              Details
            </button>
          </div>
        </div>
      </div>`
    )
    .join("");
}

/* ---------- 4.  Build popup HTML ---------------------------- */
function recipePopupHTML(d) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>${d.title}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    :root{
      --brand-primary:#4285F4;
      --brand-accent:#e8f0fe;
      --text-body:#202124;
    }
    body{
      margin:0;
      font-family:'Inter',sans-serif;
      background:var(--brand-accent);
      color:var(--text-body);
      padding:24px;
    }
    /* ---- title bar ---- */
    h1{
      background:var(--brand-primary);
      color:#fff;
      text-align:center;
      width:100%;
      padding:.6rem 1rem;
      border-radius:.75rem;
      font-size:1.6rem;
      font-weight:600;
      margin:0 0 1.2rem;
    }
    /* ---- section cards ---- */
    section.card-like{
      background:#fff;
      border-radius:.75rem;
      box-shadow:0 .25rem .75rem rgba(0,0,0,.1);
      padding:1rem;
      margin-bottom:1.2rem;
    }
    /* headings inside cards */
    h4{
      font-size:1.1rem;
      font-weight:600;
      color:var(--brand-primary);
      margin-bottom:.6rem;
    }
    ul,ol{margin-bottom:0;}
  </style>
</head>
<body>
  <h1>${d.title}</h1>

  <section class="card-like">
    <h4>Ingredients</h4>
    <ul>
      ${d.ingredients.map((i) => `<li>${i}</li>`).join("")}
    </ul>
  </section>

  <section class="card-like">
    <h4>Instructions</h4>
    <ol>
      ${d.instructions.map((i) => `<li>${i}</li>`).join("")}
    </ol>
  </section>

  <p><strong>Allergens:</strong>
     ${
       d.allergens.length
         ? d.allergens.join(", ")
         : "<span class='text-success'>None 🎉</span>"
     }
  </p>
</body>
</html>`;
}

/* ---------- 5.  Fetch & open popup -------------------------- */
async function showDetails(id) {
  try {
    const d = await (await fetch(`${API}/recipe/${id}`)).json();
    const win = window.open(
      "",
      "_blank",
      "width=720,height=700,scrollbars=yes"
    );
    win.document.write(recipePopupHTML(d));
    win.document.close();
  } catch (err) {
    alert("Error loading recipe.");
    console.error(err);
  }
}

/* ---------- 6.  Event wiring ------------------------------- */
document.addEventListener("DOMContentLoaded", init);
$("#searchBtn").addEventListener("click", search);
$("#results").addEventListener("click", (ev) => {
  const btn = ev.target.closest(".btn-details");
  if (!btn) return;
  showDetails(btn.dataset.id);
});
