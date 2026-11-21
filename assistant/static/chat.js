/* Chat accesible de Carvajal: streaming SSE, controles y feedback (diseño Stitch). */
(() => {
  "use strict";

  const form = document.getElementById("ask-form");
  const input = document.getElementById("question");
  const statusLine = document.getElementById("status");
  const conversation = document.getElementById("conversation");
  const newConversation = document.getElementById("new-conversation");
  if (!form || !input || !conversation) return;

  let controller = null;

  const setStatus = (text) => {
    if (statusLine) statusLine.textContent = text || "";
  };

  const timeLabel = () =>
    new Intl.DateTimeFormat("es", { hour: "2-digit", minute: "2-digit" }).format(new Date());

  function makeExchange(question) {
    const article = document.createElement("article");
    article.className = "flex flex-col gap-4 w-full";
    article.dataset.status = "streaming";
    article.dataset.question = question;

    const userRow = document.createElement("div");
    userRow.className = "flex flex-col gap-1 items-end w-full";
    const userLabel = document.createElement("div");
    userLabel.className = "flex items-center gap-2 mb-1 px-2 text-on-surface-variant text-sm";
    userLabel.innerHTML =
      '<span aria-hidden="true" class="material-symbols-outlined text-[20px] text-secondary">mic</span><span>Tu mensaje</span><time class="ml-2">' +
      timeLabel() +
      "</time>";
    const userBubble = document.createElement("div");
    userBubble.className = "bg-primary text-white rounded-[24px] p-4 shadow-md max-w-[85%]";
    const userText = document.createElement("p");
    userText.className = "font-body-lg text-body-lg text-white";
    userText.textContent = question;
    userBubble.append(userText);
    userRow.append(userLabel, userBubble);

    const carvaRow = document.createElement("div");
    carvaRow.className = "flex items-start gap-3 w-full";
    const avatar = document.createElement("div");
    avatar.className =
      "w-[64px] h-[64px] rounded-full overflow-hidden bg-tertiary-fixed shrink-0 border-2 border-border shadow-sm";
    const avatarImg = document.createElement("img");
    avatarImg.src = "/static/stitch/assets/carva-saludando-transparente.png";
    avatarImg.alt = "Carva, tu asistente de Carvajal";
    avatarImg.className = "w-full h-full object-cover";
    avatar.append(avatarImg);

    const card = document.createElement("div");
    card.className = "flex-1 bg-surface border border-border rounded-[24px] p-4 shadow-sm";
    const header = document.createElement("div");
    header.className = "flex items-center justify-between pb-2 border-b border-border/70 mb-2";
    const name = document.createElement("span");
    name.className = "font-label-md text-label-md text-primary";
    name.textContent = "Carva";
    const time = document.createElement("time");
    time.className = "text-sm text-on-surface-variant";
    time.textContent = timeLabel();
    header.append(name, time);

    const answer = document.createElement("div");
    answer.className = "answer-text font-body-lg text-body-lg text-on-surface space-y-2";
    const status = document.createElement("p");
    status.className = "text-sm text-on-surface-variant mt-2";
    status.textContent = "Carva está preparando la respuesta…";
    const sources = document.createElement("div");
    sources.className = "sources-container";
    const actions = document.createElement("div");
    actions.className = "flex flex-wrap items-center gap-3 mt-3";
    actions.hidden = true;
    card.append(header, status, answer, sources, actions);
    carvaRow.append(avatar, card);
    article.append(userRow, carvaRow);
    conversation.append(article);
    conversation.setAttribute("aria-busy", "true");
    return { article, status, answer, sources, actions, card };
  }

  function actionButton(label, icon) {
    const button = document.createElement("button");
    button.type = "button";
    button.className =
      "h-[52px] px-4 bg-background hover:bg-surface-container-low text-primary rounded-[16px] border border-border flex items-center gap-2 text-sm font-bold transition-all focus:outline-none focus:ring-4 focus:ring-[#BCE9FF]";
    if (icon) {
      const span = document.createElement("span");
      span.className = "material-symbols-outlined text-[24px] text-secondary";
      span.setAttribute("aria-hidden", "true");
      span.textContent = icon;
      button.append(span);
    }
    button.append(document.createTextNode(label));
    return button;
  }

  function addCopyButton(actions, card) {
    const copy = actionButton("Copiar respuesta", "content_copy");
    copy.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(card.innerText.trim());
        copy.textContent = "¡Copiado!";
        setTimeout(() => (copy.textContent = "Copiar respuesta"), 1800);
      } catch {
        copy.textContent = "No se pudo copiar";
      }
    });
    actions.append(copy);
  }

  function addFeedback(actions, messageId) {
    const up = actionButton("Útil", "thumb_up");
    const down = actionButton("No útil", "thumb_down");
    const commentRow = document.createElement("div");
    commentRow.className = "flex flex-wrap items-center gap-2 w-full mt-2";
    commentRow.hidden = true;
    const comment = document.createElement("input");
    comment.type = "text";
    comment.maxLength = 500;
    comment.placeholder = "Comentario opcional (sin datos personales)";
    comment.className =
      "flex-1 min-w-[220px] h-[52px] px-4 rounded-[14px] border-2 border-border bg-surface text-base";
    comment.setAttribute("aria-label", "Comentario opcional sobre la respuesta");
    const send = actionButton("Enviar comentario", "send");

    async function submit(rating) {
      up.classList.toggle("bg-primary", rating === "up");
      up.classList.toggle("text-white", rating === "up");
      down.classList.toggle("bg-primary", rating === "down");
      down.classList.toggle("text-white", rating === "down");
      commentRow.hidden = false;
      send.dataset.rating = rating;
      try {
        const response = await fetch("/feedback", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ message_id: messageId, rating, comment: comment.value }),
        });
        if (!response.ok) throw new Error("feedback");
        send.textContent = "Gracias, registrado";
        setStatus("Feedback registrado.");
      } catch {
        setStatus("No se pudo registrar el feedback; inténtalo de nuevo.");
      }
    }

    up.addEventListener("click", () => submit("up"));
    down.addEventListener("click", () => submit("down"));
    send.addEventListener("click", () => submit(send.dataset.rating || "up"));
    commentRow.append(comment, send);
    actions.append(up, down, commentRow);
  }

  function showError(exchange, message, requestId) {
    exchange.status.remove();
    exchange.answer.innerHTML = "";
    const paragraph = document.createElement("p");
    paragraph.className = "text-[#8A5415] font-bold";
    paragraph.textContent = message;
    exchange.answer.append(paragraph);
    if (requestId) {
      const reference = document.createElement("p");
      reference.className = "text-sm text-on-surface-variant";
      reference.textContent = "Referencia: " + requestId;
      exchange.answer.append(reference);
    }
    exchange.article.dataset.status = "error";
    exchange.actions.hidden = false;
    const retry = actionButton("Reintentar", "refresh");
    retry.addEventListener("click", async () => {
      const question = exchange.article.dataset.question || "";
      exchange.article.remove();
      await sendQuestion(question);
    });
    exchange.actions.append(retry);
    conversation.setAttribute("aria-busy", "false");
  }

  function parseChunk(chunk) {
    let event = "message";
    const data = [];
    for (const raw of chunk.split("\n")) {
      if (raw.startsWith("event:")) event = raw.slice(6).trim();
      else if (raw.startsWith("data:")) data.push(raw.slice(5).trim());
    }
    if (!data.length) return null;
    try {
      return { event, data: JSON.parse(data.join("\n")) };
    } catch {
      return null;
    }
  }

  async function consume(response, onEvent) {
    if (!response.body) throw new Error("sin stream");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let index;
      while ((index = buffer.indexOf("\n\n")) >= 0) {
        const chunk = buffer.slice(0, index);
        buffer = buffer.slice(index + 2);
        const event = parseChunk(chunk);
        if (event) onEvent(event);
      }
    }
  }

  async function sendQuestion(question) {
    const cleaned = question.trim();
    if (!cleaned) {
      input.focus();
      return;
    }
    setStatus("");
    const exchange = makeExchange(cleaned);
    controller = new AbortController();
    let firstToken = false;
    let messageId = null;
    let finished = false;

    try {
      const response = await fetch("/ask/stream", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ question: cleaned }),
        signal: controller.signal,
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "No se pudo enviar la pregunta.");
      }
      await consume(response, (event) => {
        if (event.event === "status") {
          exchange.status.textContent =
            event.data.phase === "retrieving"
              ? "Buscando en el corpus y el catálogo…"
              : "Escribiendo la respuesta…";
        } else if (event.event === "token") {
          if (!firstToken) {
            firstToken = true;
            exchange.status.textContent = "";
          }
          exchange.answer.textContent += event.data.text || "";
        } else if (event.event === "catalog") {
          exchange.status.remove();
          exchange.answer.innerHTML = event.data.html || "";
        } else if (event.event === "sources") {
          exchange.sources.innerHTML = event.data.html || "";
        } else if (event.event === "done") {
          finished = true;
          messageId = event.data.message_id || null;
          if (event.data.final_html) exchange.answer.innerHTML = event.data.final_html;
          if (exchange.status.isConnected) exchange.status.remove();
          exchange.article.dataset.status = event.data.status || "answered";
          exchange.article.dataset.provider = event.data.provider || "";
          if (messageId) {
            exchange.article.dataset.messageId = messageId;
            exchange.actions.hidden = false;
            addCopyButton(exchange.actions, exchange.card);
            addFeedback(exchange.actions, messageId);
          }
          setStatus(event.data.status === "no_evidence" ? "Sin evidencia suficiente." : "Respuesta lista.");
        } else if (event.event === "error") {
          finished = true;
          showError(exchange, event.data.message || "No se pudo responder.", event.data.request_id);
          setStatus("");
        }
      });
      if (!finished) {
        showError(exchange, "La conexión terminó antes de completar la respuesta.", null);
      }
    } catch (error) {
      if (error.name === "AbortError") {
        exchange.article.remove();
        return;
      }
      showError(exchange, error.message || "No se pudo responder en este momento.", null);
    } finally {
      conversation.setAttribute("aria-busy", "false");
      controller = null;
    }
  }

  document.querySelectorAll("[data-quick]").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.dataset.quick || "";
      form.requestSubmit();
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value;
    input.value = "";
    await sendQuestion(question);
    input.focus();
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  newConversation?.addEventListener("click", () => {
    controller?.abort();
    conversation.replaceChildren();
    conversation.setAttribute("aria-busy", "false");
    setStatus("");
    input.value = "";
    input.focus();
  });
})();
