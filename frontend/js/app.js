const API_URL = '/api';

let currentUserId = null;
let currentTransactionId = null;

// Screens
const loginScreen = document.getElementById('login-screen');
const transferScreen = document.getElementById('transfer-screen');
const voiceAuthScreen = document.getElementById('voice-auth-screen');
const errorScreen = document.getElementById('error-screen');

function showScreen(screenEl) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    screenEl.classList.add('active');
}

// Login
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        if (res.ok) {
            currentUserId = data.user_id;
            showScreen(transferScreen);
        } else {
            alert(data.detail || 'Error en login');
        }
    } catch (err) {
        console.error(err);
        alert('Error conectando al servidor');
    }
});

// Transfer
document.getElementById('transfer-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const destination = document.getElementById('tx-destination').value;
    const amount = parseFloat(document.getElementById('tx-amount').value);
    const concept = document.getElementById('tx-concept').value;
    const pin = document.getElementById('tx-pin').value;

    try {
        const res = await fetch(`${API_URL}/transfer`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: currentUserId,
                pin: pin,
                amount: amount,
                destination_account: destination,
                concept: concept
            })
        });
        const data = await res.json();

        if (res.status === 503) {
            // Flujo de Peligro
            showScreen(errorScreen);
        } else if (res.ok) {
            if (data.status === 'held') {
                // Flujo Sospechoso
                currentTransactionId = data.transaction_id;
                
                // Cargar audio base64
                if (data.audio_base64) {
                    const audioEl = document.getElementById('security-audio');
                    audioEl.src = `data:audio/mp3;base64,${data.audio_base64}`;
                }
                
                showScreen(voiceAuthScreen);
            } else {
                // Flujo Normal
                alert(`Transferencia exitosa. Nuevo saldo: $${data.new_balance}`);
                document.getElementById('transfer-form').reset();
            }
        } else {
            alert(data.detail || 'Error en la transferencia');
        }
    } catch (err) {
        console.error(err);
    }
});

// Voice Confirm
document.getElementById('voice-confirm-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const userText = document.getElementById('user-voice-response').value;

    try {
        const res = await fetch(`${API_URL}/confirm_transfer`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                transaction_id: currentTransactionId,
                user_response_text: userText
            })
        });
        const data = await res.json();
        
        if (res.ok) {
            alert(data.message);
            document.getElementById('voice-confirm-form').reset();
            showScreen(transferScreen);
        } else {
            alert(data.detail);
            showScreen(transferScreen);
        }
    } catch (err) {
        console.error(err);
    }
});

document.getElementById('logout-btn').addEventListener('click', () => {
    currentUserId = null;
    document.getElementById('transfer-form').reset();
    document.getElementById('login-form').reset();
    showScreen(loginScreen);
});

document.getElementById('return-btn').addEventListener('click', () => {
    showScreen(loginScreen);
});

