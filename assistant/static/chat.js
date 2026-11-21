/* Chat accesible de Carvajal: streaming SSE, controles y feedback. */
(() => {
  "use strict";

  const form = document.getElementById("ask-form");
  const input = document.getElementById("question");
  const statusLine = document.getElementById("status");
  const conversation = document.getElementById("conversation");
  const newConversation = document.getElementById("new-conversation");
  if (!form || !input || !conversation) return;

  let controller = null;

  function setStatus(text) {
    if (statusLine) statusLine.textContent = text || "";
  }

  function makeExchange(question) {
    const article = document.createElement("article");
    article.className = "exchange";
    article.dataset.status = "streaming";
    article.dataset.question = question;

    const user = document.createElement("div");
    user.className = "msg user";
    const userBubble = document.createElement("div");
    userBubble.className = "bubble";
    const userText = document.createElement("p");
    userText.textContent = question;
    userBubble.append(userText);
    user.append(userBubble);

    const carva = document.createElement("div");
    carva.className = "msg carva";
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "Carva";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    const status = document.createElement("p");
    status.className = "status";
    status.textContent = "Carva está preparando la respuesta…";
    const answer = document.createElement("div");
    answer.className = "answer-text";
    const sources = document.createElement("div");
    sources.className = "sources-container";
    const actions = document.createElement("div");
    actions.className = "actions";
    actions.hidden = true;
    bubble.append(status, answer, sources, actions);
    carva.append(avatar, bubble);
    article.append(user, carva);
    conversation.append(article);
    conversation.setAttribute("aria-busy", "true");
    return { article, status, answer, sources, actions, bubble };
  }

  function addCopyButton(actions, bubble) {
    const copy = document.createElement("button");
    copy.type = "button";
    copy.textContent = "Copiar respuesta";
    copy.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(bubble.innerText.trim());
        copy.textContent = "¡Copiado!";
        setTimeout(() => (copy.textContent = "Copiar respuesta"), 1800);
      } catch {
        copy.textContent = "No se pudo copiar";
      }
    });
    actions.append(copy);
  }

  function addFeedback(actions, messageId) {
    const box = document.createElement("div");
    box.className = "feedback";
    const up = document.createElement("button");
    up.type = "button";
    up.textContent = "Útil";
    const down = document.createElement("button");
    down.type = "button";
    down.textContent = "No útil";
    const commentRow = document.createElement("div");
    commentRow.className = "feedback-comment";
    commentRow.hidden = true;
    const comment = document.createElement("input");
    comment.type = "text";
    comment.maxLength = 500;
    comment.placeholder = "Comentario opcional (sin datos personales)";
    comment.setAttribute("aria-label", "Comentario opcional sobre la respuesta");
    const send = document.createElement("button");
    send.type = "button";
    send.textContent = "Enviar comentario";
    commentRow.append(comment, send);

    async function submit(rating) {
      up.classList.toggle("selected", rating === "up");
      down.classList.toggle("selected", rating === "down");
      commentRow.hidden = false;
      send.dataset.rating = rating;
      try {
        const body = new URLSearchParams({
          message_id: messageId,
          rating,
          comment: comment.value,
        });
        const response = await fetch("/feedback", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body,
        });
        if (!response.ok) throw new Error("feedback");
        box.dataset.rating = rating;
      } catch {
        setStatus("No se pudo registrar el feedback; inténtalo de nuevo.");
      }
    }

    up.addEventListener("click", () => submit("up"));
    down.addEventListener("click", () => submit("down"));
    send.addEventListener("click", () => submit(send.dataset.rating || "up"));
    box.append(up, down, commentRow);
    actions.append(box);
  }

  function showError(exchange, message, requestId) {
    exchange.status.remove();
    exchange.answer.innerHTML = "";
    const paragraph = document.createElement("p");
    paragraph.className = "warning";
    paragraph.textContent = message;
    exchange.answer.append(paragraph);
    if (requestId) {
      const reference = document.createElement("p");
      reference.className = "hint";
      reference.textContent = "Referencia: " + requestId;
      exchange.answer.append(reference);
    }
    exchange.article.dataset.status = "error";
    exchange.actions.hidden = false;
    const retry = document.createElement("button");
    retry.type = "button";
    retry.textContent = "Reintentar";
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
          const phase = event.data.phase;
          exchange.status.textContent =
            phase === "retrieving"
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
          if (event.data.final_html) {
            exchange.answer.innerHTML = event.data.final_html;
          }
          if (exchange.status.isConnected) exchange.status.remove();
          exchange.article.dataset.status = event.data.status || "answered";
          exchange.article.dataset.provider = event.data.provider || "";
          if (messageId) {
            exchange.article.dataset.messageId = messageId;
            exchange.actions.hidden = false;
            addCopyButton(exchange.actions, exchange.bubble);
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

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = input.value;
    input.value = "";
    input.style.height = "";
    await sendQuestion(question);
    input.focus();
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 200) + "px";
  });

  newConversation?.addEventListener("click", () => {
    controller?.abort();
    conversation.replaceChildren();
    conversation.setAttribute("aria-busy", "false");
    setStatus("");
    input.value = "";
    input.style.height = "";
    input.focus();
  });
})();
