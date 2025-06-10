
const API = '/api';           
async function init() {
 
  const allergens = await (await fetch(`${API}/allergens`)).json();
  const wrap = document.getElementById('allergenCheckboxes');
  wrap.innerHTML = allergens.map(a => `
    <div class="form-check col">
      <input class="form-check-input" type="checkbox" value="${a}" id="chk-${a}">
      <label class="form-check-label" for="chk-${a}">${a}</label>
    </div>`).join('');
}

function selectedAllergens () {
  return Array.from(
    document.querySelectorAll('#allergenCheckboxes input:checked')
  ).map(cb => cb.value);
}

async function search () {
  const q       = document.getElementById('searchBox').value.trim();
  const exclude = selectedAllergens();

  const params = new URLSearchParams();
  exclude.forEach(e => params.append('exclude', e));
  if (q) params.append('q', q);
  params.append('limit', '30');

  const url  = `${API}/recipes?${params.toString()}`;
  const list = await (await fetch(url)).json();
  renderResults(list);
}

function renderResults (recipes) {
  const tgt = document.getElementById('results');
  if (!recipes.length) {
    tgt.innerHTML = '<p><em>No recipes found.</em></p>';
    return;
  }
  tgt.innerHTML = recipes.map(r => `
    <div class="col-12 col-md-6 col-lg-4 mb-3">
      <div class="card shadow-sm h-100">
        <div class="card-body">
          <h5 class="card-title">${r.title}</h5>
          <p class="card-text small">
            Allergens flagged: ${r.allergens.join(', ') || '<strong>None 🎉</strong>'}
          </p>
          <button class="btn btn-sm btn-outline-secondary" onclick="showDetails(${r.id})">
            Details
          </button>
        </div>
      </div>
    </div>`).join('');
}

async function showDetails (id) {
  const d = await (await fetch(`${API}/recipe/${id}`)).json();
  const html = `
    <h4>${d.title}</h4>
    <h6>Ingredients</h6>
    <ul>${d.ingredients.map(i => `<li>${i}</li>`).join('')}</ul>
    <h6>Instructions</h6>
    <ol>${d.instructions.map(i => `<li>${i}</li>`).join('')}</ol>
    <p><small>Allergens: ${d.allergens.join(', ') || 'None'}</small></p>`;
  const w = window.open('', '_blank', 'width=600,height=600,scrollbars=yes');
  w.document.write(html);
  w.document.close();
}

document.getElementById('searchBtn').addEventListener('click', search);
document.addEventListener('DOMContentLoaded', init);
