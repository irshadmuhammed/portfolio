// Main JS - IrshadGPT Copilot + Theme Toggle
document.addEventListener("DOMContentLoaded", () => {

    // Smooth scroll
    document.querySelectorAll("a[href^='#']").forEach(anchor => {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute("href"));
            if (target) target.scrollIntoView({ behavior: "smooth" });
        });
    });

    // Theme Toggle
    const themeToggle = document.querySelector(".theme-toggle");
    if (themeToggle) {
        const icon = themeToggle.querySelector("i");
        const savedTheme = localStorage.getItem("theme");
        if (savedTheme) {
            document.documentElement.setAttribute("data-theme", savedTheme);
            if (savedTheme === "light" && icon) {
                icon.classList.remove("fa-moon");
                icon.classList.add("fa-sun");
            }
        }
        themeToggle.addEventListener("click", () => {
            const current = document.documentElement.getAttribute("data-theme");
            const next = current === "light" ? "dark" : "light";
            document.documentElement.setAttribute("data-theme", next);
            localStorage.setItem("theme", next);
            if (icon) {
                if (next === "light") { icon.classList.remove("fa-moon"); icon.classList.add("fa-sun"); }
                else { icon.classList.remove("fa-sun"); icon.classList.add("fa-moon"); }
            }
        });
    }

    // IrshadGPT Copilot
    const messagesEl = document.getElementById("copilotMessages");
    const inputEl    = document.getElementById("copilotInput");
    const sendBtn    = document.getElementById("copilotSend");
    const resetBtn   = document.getElementById("copilotReset");
    const chipsEl    = document.getElementById("copilotChips");

    if (!messagesEl || !inputEl || !sendBtn) return;

    // Minimal Markdown renderer
    function renderMarkdown(text) {
        if (!text) return "";
        let html = text
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.+?)\*/g, "<em>$1</em>")
            .replace(/`([^`]+)`/g, "<code>$1</code>")
            .replace(/^[-*] (.+)/gm, "<li>$1</li>")
            .replace(/^\d+\. (.+)/gm, "<li>$1</li>")
            .replace(/^#{1,3} (.+)/gm, "<strong>$1</strong>")
            .replace(/\n/g, "<br>");
        return html;
    }

    function scrollBottom() { messagesEl.scrollTop = messagesEl.scrollHeight; }

    // Auto-resize textarea
    inputEl.addEventListener("input", () => {
        inputEl.style.height = "auto";
        inputEl.style.height = Math.min(inputEl.scrollHeight, 80) + "px";
    });

    // Send on Enter
    inputEl.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    sendBtn.addEventListener("click", sendMessage);

    // Chip clicks
    if (chipsEl) {
        chipsEl.querySelectorAll(".copilot-chip").forEach(chip => {
            chip.addEventListener("click", () => {
                const q = chip.getAttribute("data-q");
                if (q) { inputEl.value = q; sendMessage(); }
            });
        });
    }

    // Reset
    if (resetBtn) {
        resetBtn.addEventListener("click", async () => {
            try { await fetch("/chatbot/reset/", { method: "POST", headers: { "X-CSRFToken": getCsrf() } }); } catch (e) {}
            const msgs = messagesEl.querySelectorAll(".copilot-msg");
            msgs.forEach((m, i) => { if (i > 0) m.remove(); });
            if (chipsEl) chipsEl.style.display = "flex";
        });
    }

    function getCsrf() {
        const c = document.cookie.split(";").find(c => c.trim().startsWith("csrftoken="));
        return c ? c.split("=")[1].trim() : "";
    }

    function appendMessage(role, text, sources) {
        const div = document.createElement("div");
        div.className = "copilot-msg copilot-msg-" + role;
        if (role === "assistant") {
            div.innerHTML = "<div class='copilot-msg-label'><span class='copilot-msg-avatar-sm'>MI</span>Assistant</div><div class='copilot-msg-body'>" + renderMarkdown(text) + "</div>";
            if (sources && sources.length > 0) {
                const sd = document.createElement("div");
                sd.className = "copilot-sources";
                sd.innerHTML = sources.map(s => "<span class='copilot-source-chip'>" + s.icon + " " + s.label + "</span>").join("");
                div.appendChild(sd);
            }
        } else {
            div.innerHTML = "<div class='copilot-msg-label' style='justify-content:flex-end'>You</div><div class='copilot-msg-body'>" + text.replace(/</g,"&lt;").replace(/>/g,"&gt;") + "</div>";
        }
        messagesEl.appendChild(div);
        scrollBottom();
        return div;
    }

    function showTyping() {
        const el = document.createElement("div");
        el.className = "copilot-msg copilot-msg-assistant";
        el.id = "copilotTyping";
        el.innerHTML = "<div class='copilot-msg-label'><span class='copilot-msg-avatar-sm'>MI</span>Assistant</div><div class='copilot-typing'><span></span><span></span><span></span></div>";
        messagesEl.appendChild(el);
        scrollBottom();
        return el;
    }

    function hideTyping() { const el = document.getElementById("copilotTyping"); if (el) el.remove(); }

    async function sendMessage() {
        const question = inputEl.value.trim();
        if (!question) return;
        inputEl.value = "";
        inputEl.style.height = "auto";
        sendBtn.disabled = true;
        // if (chipsEl) chipsEl.style.display = "none";
        appendMessage("user", question, null);
        showTyping();
        let sources = [];
        let fullText = "";
        try {
            const response = await fetch("/chatbot/chat/", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrf() },
                body: JSON.stringify({ question })
            });
            if (!response.ok) throw new Error("HTTP " + response.status);
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            hideTyping();
            const assistantDiv = appendMessage("assistant", "", null);
            const bodyEl = assistantDiv.querySelector(".copilot-msg-body");
            let buffer = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";
                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    const dataStr = line.slice(6).trim();
                    if (!dataStr) continue;
                    try {
                        const data = JSON.parse(dataStr);
                        if (data.token) { fullText += data.token; bodyEl.innerHTML = renderMarkdown(fullText); scrollBottom(); }
                        if (data.sources) sources = data.sources;
                        if (data.done && sources.length > 0) {
                            const sd = document.createElement("div"); sd.className = "copilot-sources";
                            sd.innerHTML = sources.map(s => "<span class='copilot-source-chip'>" + s.icon + " " + s.label + "</span>").join("");
                            assistantDiv.appendChild(sd); scrollBottom();
                        }
                    } catch (e) {}
                }
            }
        } catch (err) {
            hideTyping();
            appendMessage("assistant", "Error: " + (err.message || "Connection error. Please try again."), null);
        } finally {
            sendBtn.disabled = false;
            inputEl.focus();
        }
    }

    scrollBottom();
});


// Copilot Popup Toggle Logic
document.addEventListener("DOMContentLoaded", () => {
    const fab = document.getElementById("copilotFab");
    const popup = document.getElementById("copilotPopup");
    const closeBtn = document.getElementById("copilotClose");

    if (fab && popup) {
        fab.addEventListener("click", (e) => {
            e.stopPropagation();
            popup.classList.toggle("open");
            if (popup.classList.contains("open")) {
                const input = document.getElementById("copilotInput");
                if (input) input.focus();
            }
        });
    }

    if (closeBtn && popup) {
        closeBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            popup.classList.remove("open");
        });
    }

    // Close chatbot when clicking outside
    document.addEventListener("click", (e) => {
        if (window._copilotJustDragged) return;
        if (popup && popup.classList.contains("open")) {
            if (!popup.contains(e.target) && !fab.contains(e.target)) {
                popup.classList.remove("open");
            }
        }
    });

    // Close chatbot on Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && popup && popup.classList.contains("open")) {
            popup.classList.remove("open");
        }
    });
});

