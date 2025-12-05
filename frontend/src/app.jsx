import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";
const ENDPOINT = `${API_BASE}/v1/ai-student-qa`;

export default function App() {
  const [auth, setAuth] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [course, setCourse] = useState("");
  const [chat, setChat] = useState([]);
  const [question, setQuestion] = useState("");
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState("");

  const handleSignIn = () => {
    if (!email || !password) return setError("Email and password are required.");
    setAuth(true);
    setChat([{ who: "bot", text: `Hello ${displayName || email.split("@")[0]}, how can I help you?` }]);
  };

  const sendQuestion = async () => {
    if (!question.trim()) return;
    const q = question.trim();
    setChat([...chat, { who: "me", text: q }]);
    setQuestion("");
    try {
      const res = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          course,
          user_email: email,
          session_id: sessionId,
        }),
      });
      const data = await res.json();
      if (data.session_id && !sessionId) setSessionId(data.session_id);
      setChat((prev) => [...prev, { who: "bot", text: data.answer || "(no answer)" }]);
    } catch (err) {
      setChat((prev) => [...prev, { who: "bot", text: "Sorry, I could not process that request." }]);
    }
  };

  if (!auth)
    return (
      <div className="page center">
        <section className="card auth">
          <h1>Sign in</h1>
          <p className="muted">Demo sign-in (client side only).</p>
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <div className="row">
            <div>
              <label>Display Name</label>
              <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
            </div>
            <div>
              <label>Course (optional)</label>
              <input value={course} onChange={(e) => setCourse(e.target.value)} />
            </div>
          </div>
          <button onClick={handleSignIn}>Continue</button>
          <div className="error">{error}</div>
        </section>
      </div>
    );

  return (
    <main className="page">
      <section className="panel">
        <header>
          <h1>Student Chatbot</h1>
          <div className="muted">Signed in as {displayName || email}</div>
        </header>
        <div className="chat-wrap">
          <div className="chat-log">
            {chat.map((msg, i) => (
              <div key={i} className={`bubble ${msg.who === "me" ? "me" : "bot"}`}>
                {msg.text}
              </div>
            ))}
          </div>
          <div className="ask">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a study question..."
              onKeyDown={(e) => e.key === "Enter" && sendQuestion()}
            />
            <button onClick={sendQuestion}>Ask</button>
          </div>
        </div>
      </section>
    </main>
  );
}
