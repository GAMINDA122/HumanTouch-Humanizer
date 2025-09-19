// === Settings Theme Switcher ===
const settingsBtn = document.getElementById('settingsBtn');
const settingsPopup = document.getElementById('settingsPopup');
const lightMode = document.getElementById('lightMode');
const darkMode = document.getElementById('darkMode');

settingsBtn.addEventListener('click', () => {
  settingsPopup.style.display = (settingsPopup.style.display === 'block') ? 'none' : 'block';
});

lightMode.addEventListener('click', () => {
  document.body.classList.remove('dark-mode');
  lightMode.classList.add('selected');
  darkMode.classList.remove('selected');
});

darkMode.addEventListener('click', () => {
  document.body.classList.add('dark-mode');
  darkMode.classList.add('selected');
  lightMode.classList.remove('selected');
});

// === Existing Button Features ===
document.getElementById("advancedBtn").addEventListener("click", () => {
  alert("Advanced features coming soon 👀");
});

document.getElementById("logoutBtn").addEventListener("click", () => {
  alert("Logging out...");
});

// === Word Count & Limit Functionality ===
const aiInput = document.getElementById("aiInput");
const humanizedOutput = document.getElementById("humanizedOutput");
const inputWordCount = document.getElementById("inputWordCount");
const outputWordCount = document.getElementById("outputWordCount");
const similarityScore = document.getElementById("similarityScore");

function countWords(text) {
  if (!text) return 0;
  return text.trim().split(/\s+/).length;
}

function limitWords(text, max = 500) {
  const words = text.trim().split(/\s+/);
  if (words.length > max) {
    return words.slice(0, max).join(" ");
  }
  return text;
}

aiInput.addEventListener("input", () => {
  // ===== Input Validation to prevent code/script injection =====
  const pattern = /<\s*script.*?>.*?<\s*\/\s*script\s*>|<[^>]+>/gi;
  if (pattern.test(aiInput.value)) {
    alert("Invalid input! No code or scripts allowed.");
    location.reload(); // reload the page
    return; // stop further processing
  }

  // ===== Existing word limit functionality =====
  aiInput.value = limitWords(aiInput.value, 500);
  inputWordCount.textContent = countWords(aiInput.value);
});

humanizedOutput.addEventListener("input", () => {
  // ===== Input Validation to prevent code/script injection =====
  const pattern = /<\s*script.*?>.*?<\s*\/\s*script\s*>|<[^>]+>/gi;
  if (pattern.test(humanizedOutput.value)) {
    alert("Invalid input! No code or scripts allowed.");
    location.reload();
    return;
  }

  // ===== Existing word limit functionality =====
  humanizedOutput.value = limitWords(humanizedOutput.value, 500);
  outputWordCount.textContent = countWords(humanizedOutput.value);
});

// === 🧠 Humanize Button Functionality ===
document.querySelector(".humanize-btn").addEventListener("click", async () => {
  let aiText = aiInput.value;
  aiText = limitWords(aiText, 500); // trim if exceeds

  // ✅ ADD THIS BLOCK RIGHT HERE
  if (!aiText.trim()) {  // check for empty input
    humanizedOutput.value = "Please enter some text to humanize";
    return; // stop further processing
  }

  inputWordCount.textContent = countWords(aiText);
  aiInput.value = aiText;

  humanizedOutput.value = "Humanizing... please wait 🧠✨";
  similarityScore.textContent = "0.00%"; // reset before new output

  try {
    const response = await fetch("/humanize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: aiText }),
    });

    const data = await response.json();
    console.log("Response data:", data);

    if (data.humanized) {
      const limitedOutput = limitWords(data.humanized, 500);
      humanizedOutput.value = limitedOutput;
      outputWordCount.textContent = countWords(limitedOutput);

      // display similarity as percentage with 2 decimal points
      const percent = (data.similarity * 100).toFixed(2);
      similarityScore.textContent = `${percent}%`;
    } else if (data.error) {
      humanizedOutput.value = `Error: ${data.error}`;
      similarityScore.textContent = "Similarity: 0.00%";
    } else {
      humanizedOutput.value = "Unexpected response from server.";
      similarityScore.textContent = "Similarity: 0.00%";
    }
  } catch (error) {
    humanizedOutput.value = "❌ Error humanizing text. Make sure the server is running.";
    similarityScore.textContent = "Similarity: 0.00%";
    console.error("Humanize Error:", error);
  }
});
