function initChat(userId) {
  // use ws or wss depending on protocol
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const chatSocket = new WebSocket(
    protocol + "://" + window.location.host + "/ws/chat/user_" + userId + "/"
  );

  const log = document.getElementById('chat-log');
  const inputEl = document.getElementById('chat-message-input');
  const sendBtn = document.getElementById('chat-send');

  chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const who = data.sender_is_admin ? "Admin" : "You";
    const p = document.createElement("p");
    p.textContent = who + ": " + data.message;
    log.appendChild(p);
  };

  chatSocket.onclose = function(e) {
    console.error("Chat socket closed unexpectedly");
  };

  sendBtn.onclick = function() {
    const message = inputEl.value;
    if (!message) return;
    chatSocket.send(JSON.stringify({
      "message": message,
      "sender_is_admin": false
    }));
    inputEl.value = "";
  };
}
