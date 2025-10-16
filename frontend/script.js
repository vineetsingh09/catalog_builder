const form = document.getElementById("catalog-form");
const loading = document.getElementById("loading");
const result = document.getElementById("result");
const errorSection = document.getElementById("error");
const resultName = document.getElementById("result-name");
const resultDescription = document.getElementById("result-description");
const resultBullets = document.getElementById("result-bullets");
const resultBlurb = document.getElementById("result-blurb");
const resultImages = document.getElementById("result-images");
const resultSources = document.getElementById("result-sources");

const API_BASE_URL = import.meta?.env?.VITE_API_BASE_URL || window.API_BASE_URL || "http://localhost:8000";

function setVisibility(element, isVisible) {
  element.classList.toggle("hidden", !isVisible);
}

function renderMarkdown(text) {
  const html = text
    .replace(/\r?\n\r?\n/g, "</p><p>")
    .replace(/\r?\n/g, "<br />")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>");
  return `<p>${html}</p>`;
}

function resetResult() {
  resultName.textContent = "";
  resultDescription.innerHTML = "";
  resultBullets.innerHTML = "";
  resultBlurb.textContent = "";
  resultImages.innerHTML = "";
  resultSources.innerHTML = "";
}

async function handleSubmit(event) {
  event.preventDefault();
  const formData = new FormData(form);
  const payload = {
    product_name: formData.get("productName"),
    keywords: (formData.get("keywords") || "")
      .split(",")
      .map((kw) => kw.trim())
      .filter(Boolean),
    country: formData.get("country"),
    language: formData.get("language"),
  };

  resetResult();
  setVisibility(result, false);
  setVisibility(errorSection, false);
  setVisibility(loading, true);

  try {
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();

    resultName.textContent = payload.product_name;
    resultDescription.innerHTML = renderMarkdown(data.product_description);
    resultBullets.innerHTML = data.bullet_points
      .map((point) => `<li>${point}</li>`)
      .join("");
    resultBlurb.textContent = data.marketing_blurb;
    resultImages.innerHTML = data.image_urls
      .map((url) => `<figure><img src="${url}" alt="${payload.product_name}" /></figure>`)
      .join("");

    if (data.sources?.length) {
      const items = data.sources
        .map(
          (source) =>
            `<li><a href="${source.url}" target="_blank" rel="noopener noreferrer">${source.name}</a></li>`
        )
        .join("");
      resultSources.innerHTML = `<h3>Where to buy</h3><ul>${items}</ul>`;
    }

    setVisibility(result, true);
  } catch (err) {
    console.error(err);
    errorSection.textContent = err.message || "Something went wrong.";
    setVisibility(errorSection, true);
  } finally {
    setVisibility(loading, false);
  }
}

form.addEventListener("submit", handleSubmit);
