let mapData = { x: [], y: [], z: [], text: [] };
let socket;
let currentQueryCoords = null;

// INIT
async function initMap() {
    const response = await fetch('/api/map-data');
    const data = await response.json();
    
    mapData.x = data.coords.map(c => c[0]);
    mapData.y = data.coords.map(c => c[1]);
    mapData.z = data.coords.map(c => c[2]);
    mapData.text = data.texts;

    // Draw the "Universe" (All Grey)
    drawGraph([], []);
}

// GLOBAL VARIABLE TO STORE YOUR VIEW
let userCamera = null; 

function drawGraph(yellowIndices=[], greenIndices=[]) {
    const graphDiv = document.getElementById('vector-graph');

    // 1. SAVE CAMERA POSITION (If graph already exists)
    if (graphDiv.layout && graphDiv.layout.scene && graphDiv.layout.scene.camera) {
        userCamera = graphDiv.layout.scene.camera;
    }

    const traces = [];

    // --- (Your Traces 1, 2, 3, 4 code remains exactly the same) ---
    // 1. BASE LAYER
    const allIndices = mapData.x.map((_, i) => i);
    const greyIndices = allIndices.filter(i => !yellowIndices.includes(i) && !greenIndices.includes(i));
    traces.push({
        x: greyIndices.map(i => mapData.x[i]),
        y: greyIndices.map(i => mapData.y[i]),
        z: greyIndices.map(i => mapData.z[i]),
        mode: 'markers', type: 'scatter3d',
        text: greyIndices.map(i => mapData.text[i]),
        hoverinfo: 'text',
        marker: { size: 3, color: '#C0C0C0', opacity: 0.3 }, 
        name: 'Latent Data'
    });

    // 2. RETRIEVED LAYER
    if (yellowIndices.length > 0) {
        traces.push({
            x: yellowIndices.map(i => mapData.x[i]),
            y: yellowIndices.map(i => mapData.y[i]),
            z: yellowIndices.map(i => mapData.z[i]),
            mode: 'markers', type: 'scatter3d',
            text: yellowIndices.map(i => mapData.text[i]),
            hoverinfo: 'text',
            marker: { size: 6, color: '#ff8205ff', symbol: 'circle', opacity: 0.9 },
            name: 'Candidates'
        });
    }

    // 3. RERANKED LAYER
    if (greenIndices.length > 0) {
        traces.push({
            x: greenIndices.map(i => mapData.x[i]),
            y: greenIndices.map(i => mapData.y[i]),
            z: greenIndices.map(i => mapData.z[i]),
            mode: 'markers', type: 'scatter3d',
            text: greenIndices.map(i => mapData.text[i]),
            hoverinfo: 'text',
            marker: { size: 8, color:'#e00400ff', symbol: 'diamond', opacity: 1 },
            name: 'Trusted Source'
        });
    }

    // 4. QUERY STAR
    if (currentQueryCoords) {
        traces.push({
            x: [currentQueryCoords[0]], y: [currentQueryCoords[1]], z: [currentQueryCoords[2]],
            mode: 'markers', type: 'scatter3d',
            text: ['Active Query Protocol'],
            marker: { size: 12, color: '#ff0099ff', symbol: 'cross' },
            name: 'QUERY'
        });
    }

    // --- LAYOUT ---
    const axisStyle = {
        showgrid: true, gridcolor: '#E0E0E0', gridwidth: 1,
        zeroline: true, zerolinecolor: '#333', zerolinewidth: 4,
        showbackground: false, showticklabels: false,
        showline: true, linewidth: 6, linecolor: '#333'
    };

    // 2. USE SAVED CAMERA (Or default if first load)
    const cameraSettings = userCamera ? userCamera : { eye: {x: 5.5, y: 5.5, z: 2.5} };

    const layout = {
        paper_bgcolor: '#F9F9F5',
        plot_bgcolor: '#F9F9F5',
        showlegend: false,
        margin: {l:0, r:0, b:0, t:0},
        scene: {
            xaxis: { ...axisStyle, linecolor: '#ff0000ff', title: '' },
            yaxis: { ...axisStyle, linecolor: '#33ff00ff', title: '' },
            zaxis: { ...axisStyle, linecolor: '#1900ffff', title: '' },
            // APPLY THE SAVED CAMERA HERE
            camera: cameraSettings,
            aspectmode: 'cube' 
        }
    };

    Plotly.react('vector-graph', traces, layout);
}

// SOCKET HANDLING
const input = document.getElementById('user-input');
const historyDiv = document.getElementById('chat-history');

// Connect WS
socket = new WebSocket(`ws://${window.location.host}/ws/chat`);
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'log') {
        addLog(data.message);
    } 
    else if (data.type === 'map_update') {
        if (data.step === 'query') {
            currentQueryCoords = data.coords;
            drawGraph(); // Draw Red Star
        }
        else if (data.step === 'retrieval') {
            drawGraph(data.indices, []); // Draw Yellow dots
        }
        else if (data.step === 'rerank') {
            drawGraph([], data.indices); // Draw Green dots (clear yellow)
        }
    }
    else if (data.type === 'token') {
        // Stream tokens to the last message div
        const lastMsg = historyDiv.lastElementChild;
        if (!lastMsg.classList.contains('bot-msg')) {
            addMessage("SYSTEM", "", "bot-msg");
        }
        historyDiv.lastElementChild.innerHTML += data.content;
        historyDiv.scrollTop = historyDiv.scrollHeight;
    }
    else if (data.type === 'token') {
        const lastMsg = historyDiv.lastElementChild;
        if (!lastMsg.classList.contains('bot-msg')) {
            addMessage("SYSTEM", "", "bot-msg");
        }
        
        // Append the new character
        historyDiv.lastElementChild.innerHTML += data.content;
        
        // --- FORCE SCROLL TO BOTTOM ---
        historyDiv.scrollTop = historyDiv.scrollHeight;
    }
};

input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const text = input.value;
        input.value = '';
        addMessage("USER", text, "user-msg");
        socket.send(text);
    }
});

function addLog(text) {
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerText = `>> ${text}`;
    historyDiv.appendChild(div);
    
    // Auto-scroll on logs too
    historyDiv.scrollTop = historyDiv.scrollHeight;
}

function addMessage(role, text, className) {
    const div = document.createElement('div');
    div.className = `message ${className}`;
    div.innerHTML = `<strong>${role}:</strong> <br>${text}`; // Added <br> for spacing
    historyDiv.appendChild(div);
    
    // Auto-scroll on new message
    historyDiv.scrollTop = historyDiv.scrollHeight;
}

initMap();