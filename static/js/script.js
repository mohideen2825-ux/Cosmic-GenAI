/**
 * ComicCraft – Frontend Interactive Logic
 * Handles form validation, dynamic loading indicators, inspiration chips,
 * and custom setting visibility toggles.
 */

document.addEventListener("DOMContentLoaded", () => {
  const comicForm = document.getElementById("comicForm");
  const generateBtn = document.getElementById("generateBtn");
  const loadingOverlay = document.getElementById("loadingOverlay");
  const loadingPhaseText = document.getElementById("loadingPhaseText");
  const progressBarFill = document.getElementById("progressBarFill");
  
  const settingSelect = document.getElementById("settingSelect");
  const customSettingContainer = document.getElementById("customSettingContainer");
  const customSettingInput = document.getElementById("customSettingInput");

  // Toggle custom setting input visibility
  if (settingSelect && customSettingContainer) {
    settingSelect.addEventListener("change", (e) => {
      if (e.target.value.toLowerCase() === "custom") {
        customSettingContainer.style.display = "block";
        if (customSettingInput) customSettingInput.focus();
      } else {
        customSettingContainer.style.display = "none";
      }
    });
  }

  // Inspiration Chip Quick-Fill
  const chipButtons = document.querySelectorAll(".chip-btn");
  chipButtons.forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt") || "";
      const character = chip.getAttribute("data-character") || "";
      const setting = chip.getAttribute("data-setting") || "";
      const tone = chip.getAttribute("data-tone") || "";
      const artStyle = chip.getAttribute("data-style") || "";

      const promptInput = document.getElementById("storyPrompt");
      const charInput = document.getElementById("characterName");

      if (promptInput) promptInput.value = prompt;
      if (charInput) charInput.value = character;

      // Select setting
      if (settingSelect) {
        let matched = false;
        for (let opt of settingSelect.options) {
          if (opt.value.toLowerCase() === setting.toLowerCase()) {
            settingSelect.value = opt.value;
            matched = true;
            break;
          }
        }
        if (!matched && customSettingContainer && customSettingInput) {
          settingSelect.value = "Custom";
          customSettingContainer.style.display = "block";
          customSettingInput.value = setting;
        } else if (customSettingContainer) {
          customSettingContainer.style.display = "none";
        }
      }

      // Check tone radio
      const toneRadio = document.querySelector(`input[name="tone"][value="${tone}"]`);
      if (toneRadio) toneRadio.checked = true;

      // Check art style radio
      const styleRadio = document.querySelector(`input[name="art_style"][value="${artStyle}"]`);
      if (styleRadio) styleRadio.checked = true;

      // Smooth scroll to form
      if (promptInput) {
        promptInput.scrollIntoView({ behavior: "smooth", block: "center" });
        promptInput.focus();
      }
    });
  });

  function startLoadingAnimation() {
    if (!loadingOverlay) return;
    loadingOverlay.style.display = "flex";

    const selectedPanelRadio = document.querySelector('input[name="panel_count"]:checked');
    const panelCount = selectedPanelRadio ? selectedPanelRadio.value : "5";

    const dynamicSteps = [
      { text: `Summoning Gemini Flash for ${panelCount}-panel outline...`, progress: 18, time: 0 },
      { text: `Expanding narration & character dialogue with Gemini Pro...`, progress: 38, time: 2500 },
      { text: `Generating ${panelCount} comic illustrations with FLUX / Stable Diffusion...`, progress: 68, time: 5500 },
      { text: `Composing comic layout & compiling high-res PDF...`, progress: 90, time: 9500 },
      { text: `Almost ready! Finalizing your ${panelCount}-panel comic book...`, progress: 98, time: 13000 }
    ];

    dynamicSteps.forEach((step) => {
      setTimeout(() => {
        if (loadingPhaseText) loadingPhaseText.textContent = step.text;
        if (progressBarFill) progressBarFill.style.width = `${step.progress}%`;
      }, step.time);
    });
  }

  // Handle Form Submission
  if (comicForm) {
    comicForm.addEventListener("submit", (e) => {
      const promptInput = document.getElementById("storyPrompt");
      const charInput = document.getElementById("characterName");

      if (!promptInput || promptInput.value.trim().length < 3) {
        alert("Please describe your comic story idea (at least 3 characters).");
        if (promptInput) promptInput.focus();
        e.preventDefault();
        return;
      }

      if (!charInput || charInput.value.trim().length === 0) {
        alert("Please enter the name of your main character.");
        if (charInput) charInput.focus();
        e.preventDefault();
        return;
      }

      // Prevent duplicate submissions and disable button
      if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = `<span>GENERATING COMIC...</span>`;
      }

      // Trigger multi-step loading sequence
      startLoadingAnimation();
    });
  }
});
