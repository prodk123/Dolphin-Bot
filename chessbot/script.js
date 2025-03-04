async function sendMove() {
    let moveData = {
        initial: { row: 6, col: 4 },
        final: { row: 4, col: 4 }
    };

    console.log("Sending move:", moveData); // Debugging

    let response = await fetch("http://127.0.0.1:5000/move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(moveData),
    });

    let data = await response.json();
    console.log("Response from server:", data); // Debugging

    if (data.ai_move) {
        document.getElementById("result").innerText =
            `Bot moved from (${data.ai_move.initial.row}, ${data.ai_move.initial.col}) to (${data.ai_move.final.row}, ${data.ai_move.final.col})`;
    } else {
        document.getElementById("result").innerText = "Invalid move!";
    }
}

