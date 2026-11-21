/* Interacciones portadas del prototipo Stitch: confirmación, minimizar y voz visual. */
(() => {
  "use strict";

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let timerInterval = null;

  const $ = (id) => document.getElementById(id);
  const fullCard = () => $("confirmation-full");
  const compactCard = () => $("confirmation-compact");
  const countdown = () => $("confirmation-countdown");
  const progress = () => $("confirmation-progress");

  function focusFirst(container) {
    const target = container?.querySelector("button, a[href]");
    if (target) target.focus();
  }

  function minimizeToChat() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    const full = fullCard();
    const compact = compactCard();
    if (!full || !compact) return;
    if (reducedMotion.matches) {
      full.hidden = true;
      compact.hidden = false;
      focusFirst(compact);
      return;
    }
    full.classList.remove("max-h-[1400px]", "opacity-100", "scale-100");
    full.classList.add(
      "max-h-0",
      "opacity-0",
      "scale-95",
      "overflow-hidden",
      "!p-0",
      "!mb-0",
      "!border-0",
    );
    full.style.pointerEvents = "none";
    window.setTimeout(() => {
      full.hidden = true;
      compact.hidden = false;
      compact.classList.add("ring-4", "ring-[#00B5E5]/40", "pulse-highlight");
      window.setTimeout(() => {
        compact.classList.remove("ring-4", "ring-[#00B5E5]/40", "pulse-highlight");
      }, 1200);
      focusFirst(compact);
    }, 450);
  }

  function expandFullCard() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
    const full = fullCard();
    const compact = compactCard();
    if (!full || !compact) return;
    compact.hidden = true;
    full.hidden = false;
    if (!reducedMotion.matches) {
      full.classList.remove("max-h-0", "opacity-0", "scale-95", "overflow-hidden", "!p-0", "!mb-0", "!border-0");
      full.classList.add("max-h-[1400px]", "opacity-100", "scale-100");
    }
    full.style.pointerEvents = "";
    focusFirst(full);
  }

  function toggleFullCard() {
    const full = fullCard();
    if (!full) return;
    if (full.hidden || full.classList.contains("max-h-0")) expandFullCard();
    else minimizeToChat();
  }

  function startCountdown(seconds = 10) {
    if (timerInterval) clearInterval(timerInterval);
    const text = countdown();
    const bar = progress();
    let remaining = seconds;
    const render = () => {
      if (text) text.textContent = `Minimizando al chat en ${remaining}s`;
      if (bar) bar.style.width = `${((seconds - remaining) / seconds) * 100}%`;
    };
    render();
    timerInterval = window.setInterval(() => {
      remaining -= 1;
      render();
      if (remaining <= 0) {
        clearInterval(timerInterval);
        timerInterval = null;
        minimizeToChat();
      }
    }, 1000);
  }

  function announce(message) {
    const live = $("voice-status");
    if (live) live.textContent = message;
  }

  function initConfirmation() {
    const container = $("confirmation");
    if (!container) return;
    const seconds = Number(container.dataset.seconds || "10") || 10;
    document.querySelectorAll("[data-minimize]").forEach((button) => {
      button.addEventListener("click", minimizeToChat);
    });
    document.querySelectorAll("[data-expand]").forEach((button) => {
      button.addEventListener("click", expandFullCard);
    });
    if (!container.dataset.static) startCountdown(seconds);
  }

  document.addEventListener("DOMContentLoaded", () => {
    initConfirmation();
    document.querySelectorAll("[data-voice]").forEach((button) => {
      button.addEventListener("click", () => {
        announce("La voz estará disponible próximamente.");
      });
    });
  });

  window.minimizeToChat = minimizeToChat;
  window.expandFullCard = expandFullCard;
  window.toggleFullCard = toggleFullCard;
  window.startCountdown = startCountdown;
  window.initConfirmation = initConfirmation;
})();
