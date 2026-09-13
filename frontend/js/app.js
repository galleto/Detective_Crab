// Prefijo común para que el frontend use la API servida por FastAPI.
const API_URL = '/api';

// Estado mínimo de la sesión y de la transferencia retenida.
let currentUserId = null;
let currentTransactionId = null;
let currentTxAmount = 0;
let currentTxDestination = '';
let currentTxConcept = '';

// Referencias a las vistas que se alternan durante el flujo bancario.
const welcomeScreen = document.getElementById('welcome-screen');
const loginScreen = document.getElementById('login-screen');
const transferScreen = document.getElementById('transfer-screen');
const voiceAuthScreen = document.getElementById('voice-auth-screen');
const errorScreen = document.getElementById('error-screen');
const receiptScreen = document.getElementById('receipt-screen');

const btnIniciarApp = document.getElementById('btn-iniciar-app');
if (btnIniciarApp) {
    btnIniciarApp.addEventListener('click', (e) => {
        e.preventDefault();
        showScreen(loginScreen);
    });
}

function showScreen(screenEl) {
    // Solo una pantalla permanece visible a la vez.
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    screenEl.classList.add('active');
}

function showReceipt(amount, destination, concept, txId) {
    document.getElementById('receipt-amount').textContent = `$${parseFloat(amount).toFixed(2)}`;
    document.getElementById('receipt-destination').textContent = destination;
    document.getElementById('receipt-source').textContent = currentUserId || 'Cuenta Principal';
    document.getElementById('receipt-concept').textContent = concept || 'N/A';
    document.getElementById('receipt-id').textContent = txId || Math.floor(Math.random() * 1000000000).toString();
    
    const now = new Date();
    const dateStr = now.toLocaleDateString('es-MX', { year: 'numeric', month: '2-digit', day: '2-digit' });
    const timeStr = now.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
    
    document.getElementById('receipt-date').textContent = dateStr;
    document.getElementById('receipt-time').textContent = timeStr;
    
    showScreen(receiptScreen);
}

// Envía las credenciales y conserva el identificador de usuario recibido.
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

// Envía la transferencia y dirige la interfaz según el nivel de riesgo.
document.getElementById('transfer-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const destination = document.getElementById('tx-destination').value;
    const amount = parseFloat(document.getElementById('tx-amount').value);
    const concept = document.getElementById('tx-concept').value;
    const pin = document.getElementById('tx-pin').value;
    
    currentTxAmount = amount;
    currentTxDestination = destination;
    currentTxConcept = concept;

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
            // El PIN invertido activa la pantalla de alerta silenciosa.
            showScreen(errorScreen);
        } else if (res.ok) {
            if (data.status === 'held') {
                // La API retuvo la operación y devolvió el audio de seguridad.
                currentTransactionId = data.transaction_id;
                
                // El audio llega embebido para poder reproducirse sin otra ruta.
                if (data.audio_base64) {
                    const audioEl = document.getElementById('security-audio');
                    audioEl.src = `data:audio/mp3;base64,${data.audio_base64}`;
                }
                
                // Mostrar texto de la IA en pantalla
                const spokenTextEl = document.getElementById('ai-spoken-text');
                if (spokenTextEl && data.spoken_text) {
                    spokenTextEl.textContent = `"${data.spoken_text}"`;
                }
                
                showScreen(voiceAuthScreen);
            } else {
                // La API aprobó directamente la transferencia.
                document.getElementById('transfer-form').reset();
                showReceipt(currentTxAmount, currentTxDestination, currentTxConcept, data.transaction_id);
            }
        } else {
            alert(data.detail || 'Error en la transferencia');
        }
    } catch (err) {
        console.error(err);
    }
});

// Envía la respuesta del usuario para que Gemini decida si liberar el hold.
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
            document.getElementById('voice-confirm-form').reset();
            showReceipt(currentTxAmount, currentTxDestination, currentTxConcept, currentTransactionId);
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

document.getElementById('receipt-return-btn').addEventListener('click', () => {
    showScreen(transferScreen);
});

