document.addEventListener("DOMContentLoaded", () => {
  const btnSignIn = document.getElementById("btnSignIn");
  const authPage = document.getElementById("authPage");
  const chatPage = document.getElementById("chatPage");
  const chatLog = document.getElementById("chatLog");
  const sendBtn = document.getElementById("sendBtn");
  const questionInput = document.getElementById("question");
  const userBadge = document.getElementById("userBadge");

  // API URL (Docker vs local)
  const API_BASE =
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
      ? "http://127.0.0.1:8000"
      : "http://backend:8000";
  const ENDPOINT = `${API_BASE}/v1/ai-student-qa`;

  // --- Sign in handler ---
  btnSignIn.addEventListener("click", (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const name = document.getElementById("displayName").value.trim() || email;
    const course = document.getElementById("course").value.trim() || "General";

    if (!email || !password) {
      alert("Please enter email and password.");
      return;
    }

    localStorage.setItem("user", JSON.stringify({ email, name, course }));

    // Switch to chat view
    authPage.classList.add("hide");
    chatPage.classList.remove("hide");
    userBadge.textContent = `Signed in as ${name} — ${course}`;
  });

  // --- Send question handler ---
  sendBtn.addEventListener("click", async () => {
    const query = questionInput.value.trim();
    if (!query) return;

    // Add user message
    const me = document.createElement("div");
    me.className = "bubble me";
    me.textContent = query;
    chatLog.appendChild(me);
    questionInput.value = "";
    chatLog.scrollTop = chatLog.scrollHeight;

    try {
      const response = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();

      const bot = document.createElement("div");
      bot.className = "bubble bot";
      bot.textContent = data.answer || "No response from AI.";
      chatLog.appendChild(bot);
      chatLog.scrollTop = chatLog.scrollHeight;
    } catch (err) {
      console.error(err);
      const errorDiv = document.createElement("div");
      errorDiv.className = "bubble bot";
      errorDiv.textContent = "⚠️ Backend not reachable.";
      chatLog.appendChild(errorDiv);
    }
  });
});
