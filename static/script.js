


async function loginAndGlow() {
    const username = document.getElementById(`usernameInput`).value;
    const response = await fetch("/get-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username })
    });

    const data = await response.json();
    if (response.ok) {
        const tokenBox = document.getElementById("tokenBox");
        tokenBox.value = data.token;

        document.getElementById("tokenSection").classList.remove("hidden")
        showAboveToken("JWT Token generated below", "flash glow");
    } else {
        document.getElementById("tokenSection").classList.add("hidden");
        document.getElementById("rightAboveTokenSection").classList.add("hidden");
        showResponse(data.error, "fail flash");
    }
}


async function unlockGlow() {
    const token = document.getElementById("tokenBox").value.trim();
    showResponse("Token sent! Check console for details if needed.", "glow flash")

    const response = await fetch("/secure-endpoint", {
        method: "GET",
        headers: { Authorization: "Bearer " + token }
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

    className.split(" ").forEach(c => {
        box.classList.add(c);
    });
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

    const chatArea = document.getElementById("chatArea");
    chatArea.classList.remove("hidden");
}


async function sendMessage(roomID) {
    const input = document.getElementById("messageInput");
    const text = input.value.trim();
    
    if (!text) {
        return
    }

    const response = await fetch(`/room/${roomID}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
    });
    const data = await response.json();

    const msgDiv = document.createElement("div");
    msgDiv.textContent = data.message;
    document.getElementById("messages").appendChild(msgDiv);

    input.value = ""
}

function showAboveToken(message, className = "") {
    const box = document.getElementById("rightAboveTokenSection");

    box.textContent = message;
    box.classList.remove("glow", "fail", "shake", "flash", "hidden");
    void box.offsetWidth;

    if (className) {
        className.split(" ").forEach(c => {
            box.classList.add(c);
        });
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