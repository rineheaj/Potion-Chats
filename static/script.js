
let messageInterval = null;


// function authHeaders() {
//     const token = localStorage.getItem("jwt");
//     return {
//         "Content-Type": "application/json",
//         "Authorization": `Bearer ${token}`
//     };
// }

async function loginAndGlow() {
    const code = document.getElementById(`usernameInput`).value;
    const displayName = document.getElementById("displayNameInput").value.trim();
    const response = await fetch("/get-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: code, displayName }),
        credentials: "same-origin"
    });

    const data = await response.json();
    if (response.ok) {
        window.location.href = "/rooms";
    } else {
        showResponse(data.error, "fail flash");
    }
}


async function unlockGlow() {
    showResponse("Token sent! Check console for details if needed.", "glow flash")

    const response = await fetch("/secure-endpoint", {
        method: "GET",
        credentials: "same-origin"
    });
    const data = await response.json();

    if (response.ok) {

        showResponse(data.message, "glow");
    } else {
        showResponse(data.error, "fail shake");
    }
}

function showResponse(message, className) {
    const box = document.getElementById("response");
    box.textContent = message;
    box.classList.remove("glow", "fail", "shake", "flash");
    void box.offsetWidth;
    className.split(" ").forEach(c => box.classList.add(c));
    box.classList.remove("hidden")
}


async function submitGuess(roomID) {
    const input = document.getElementById("guessInput");
    const responseBox = document.getElementById("guessResponse");
    const guess = parseInt(input.value, 10);

    if (!guess || guess < 1 || guess > 5) {
        responseBox.textContent = "Pick a number 1-5";
        responseBox.classList.remove("hidden");
        return;
    }

    const response = await fetch(`/room/${roomID}/guess`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ guess })
    });

    const data = await response.json();
    responseBox.textContent = data.result;
    responseBox.classList.remove("hidden");

    if (data.result.startsWith("Correct")) {
        showChatInterface(roomID);
    }
}

function showChatInterface(roomID) {
    document.getElementById("guessSection").classList.add("hidden");
    document.getElementById("chatArea").classList.remove("hidden");

    fetchMessages(roomID);

    if (messageInterval) clearInterval(messageInterval);
    messageInterval = setInterval(() => fetchMessages(roomID), 2000)
}

async function fetchMessages(roomID) {
  const response = await fetch(`/room/${roomID}/messages`, {
    method: "GET",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) return;

  const msgs = await response.json();
  const container = document.getElementById("messages");
  const currentUser = container.dataset.currentUser;
  container.innerHTML = "";

  msgs.forEach(entry => {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("msg-bubble");

    if (entry.user === currentUser) {
        msgDiv.classList.add("mine");
    } else {
        msgDiv.classList.add("other");
    }


    const userSpan = document.createElement("span");
    userSpan.classList.add("msg-user");
    userSpan.textContent = entry.user;

    const textSpan = document.createElement("span");
    textSpan.classList.add("msg-text");
    textSpan.textContent = entry.message;

    msgDiv.appendChild(userSpan);
    msgDiv.appendChild(textSpan);

  });
}

async function sendMessage(roomID) {
    const input = document.getElementById("messageInput");
    const text = input.value.trim();
    
    if (!text) return;
    
    await fetch(`/room/${roomID}/chat`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
    });

    input.value = ""
}

function showAboveToken(message, className = "") {
    const box = document.getElementById("rightAboveTokenSection");

    box.textContent = message;
    box.classList.remove("glow", "fail", "shake", "flash", "hidden");
    void box.offsetWidth;

    if (className) {
        className.split(" ").forEach(c => box.classList.add(c));
    }
}


document.addEventListener("DOMContentLoaded", () => {
  const guessBtn = document.getElementById("guessBtn");
  if (guessBtn) {
    guessBtn.addEventListener("click", () =>
      submitGuess(guessBtn.dataset.roomId)
    );
  }

  const sendBtn = document.getElementById("sendMsgBtn");
  if (sendBtn) {
    sendBtn.addEventListener("click", () =>
      sendMessage(sendBtn.dataset.roomId)
    );
  }
});