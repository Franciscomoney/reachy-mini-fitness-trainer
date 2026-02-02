/**
 * Reachy Mini Fitness Trainer - Main JavaScript
 */

// State
let ws = null;
let isRunning = false;
let frameInterval = null;
let durationInterval = null;
let startTime = null;
let lastRepCount = 0;

// DOM Elements
const elements = {};

// Audio playback
let audioQueue = [];
let isPlayingAudio = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initElements();
    attachEventListeners();
    checkStatus();
    console.log('Reachy Mini Fitness Trainer initialized');
});

function initElements() {
    elements.video = document.getElementById('video');
    elements.canvas = document.getElementById('canvas');
    elements.overlay = document.getElementById('overlay');
    elements.feedback = document.getElementById('feedback');
    elements.repOverlay = document.getElementById('repOverlay');
    elements.repCount = document.getElementById('repCount');
    elements.angleOverlay = document.getElementById('angleOverlay');
    elements.angleValue = document.getElementById('angleValue');
    elements.progressRing = document.getElementById('progressRing');
    elements.progressCount = document.getElementById('progressCount');
    elements.targetReps = document.getElementById('targetReps');
    elements.startBtn = document.getElementById('startBtn');
    elements.stopBtn = document.getElementById('stopBtn');
    elements.duration = document.getElementById('duration');
    elements.reachyDot = document.getElementById('reachyDot');
    elements.reachyStatus = document.getElementById('reachyStatus');
    elements.ttsDot = document.getElementById('ttsDot');
    elements.ttsStatus = document.getElementById('ttsStatus');
    elements.bodyStatus = document.getElementById('bodyStatus');
    elements.bodyStatusText = document.getElementById('bodyStatusText');
    elements.robotStage = document.getElementById('robotStage');
    elements.moodEmoji = document.getElementById('moodEmoji');
    elements.moodText = document.getElementById('moodText');

    elements.phases = {
        standing: document.getElementById('phaseStanding'),
        descending: document.getElementById('phaseDown'),
        bottom: document.getElementById('phaseDown'),
        ascending: document.getElementById('phaseUp')
    };
}

function attachEventListeners() {
    elements.startBtn.onclick = startWorkout;
    elements.stopBtn.onclick = stopWorkout;
}

async function checkStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();

        elements.targetReps.textContent = data.target_reps;

        elements.reachyDot.className = 'status-dot ' + (data.reachy_connected ? 'green' : 'red');
        elements.reachyStatus.textContent = data.reachy_connected ? 'Connected' : 'Simulation';

        elements.ttsDot.className = 'status-dot ' + (data.tts_enabled ? 'green' : 'red');
        elements.ttsStatus.textContent = data.tts_enabled ? data.tts_provider : 'Disabled';
    } catch (e) {
        console.error('Status check failed:', e);
    }
}

async function startWorkout() {
    elements.feedback.textContent = 'Requesting camera access...';
    elements.startBtn.disabled = true;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
            audio: false
        });

        elements.video.srcObject = stream;
        await new Promise(resolve => {
            elements.video.onloadedmetadata = () => {
                elements.video.play();
                resolve();
            };
        });

        elements.overlay.classList.add('hidden');
        elements.repOverlay.style.display = 'block';
        elements.angleOverlay.style.display = 'block';
        elements.feedback.textContent = 'Connecting...';

        // Connect WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(`${protocol}//${window.location.host}/ws/workout`);

        ws.onopen = () => {
            ws.send(JSON.stringify({ type: 'start' }));
            isRunning = true;
            elements.stopBtn.disabled = false;
            startTime = Date.now();
            elements.feedback.textContent = 'GO! Start squatting!';

            // Set robot to watching state
            setRobotState('watching');

            frameInterval = setInterval(sendFrame, 100);
            durationInterval = setInterval(updateDuration, 1000);
        };

        ws.onmessage = (event) => handleMessage(JSON.parse(event.data));

        ws.onerror = (e) => {
            console.error('WebSocket error:', e);
            elements.feedback.textContent = 'Connection error. Refresh page.';
            elements.startBtn.disabled = false;
        };

        ws.onclose = () => {
            if (isRunning) stopWorkout();
        };

    } catch (e) {
        console.error('Camera error:', e);
        elements.feedback.textContent = e.name === 'NotAllowedError'
            ? 'Camera access denied. Please allow camera.'
            : 'Camera error: ' + e.message;
        elements.startBtn.disabled = false;
    }
}

function stopWorkout() {
    isRunning = false;

    if (frameInterval) {
        clearInterval(frameInterval);
        frameInterval = null;
    }
    if (durationInterval) {
        clearInterval(durationInterval);
        durationInterval = null;
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'stop' }));
        ws.close();
    }

    elements.startBtn.disabled = false;
    elements.stopBtn.disabled = true;
    setRobotState('idle');
}

function sendFrame() {
    if (!isRunning || !elements.video.videoWidth) return;

    elements.canvas.width = 640;
    elements.canvas.height = 480;
    const ctx = elements.canvas.getContext('2d');
    ctx.drawImage(elements.video, 0, 0, 640, 480);

    const imageData = elements.canvas.toDataURL('image/jpeg', 0.7);

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'frame', image: imageData }));
    }
}

function handleMessage(data) {
    if (data.type === 'audio') {
        queueAudio(data.data, data.format);
    } else if (data.type === 'pose') {
        if (data.pose_detected) {
            elements.bodyStatus.style.display = 'block';
            elements.bodyStatus.className = 'body-status detected';
            elements.bodyStatusText.textContent = '✓ Pose detected';

            elements.repCount.textContent = data.rep_count || 0;
            elements.progressCount.textContent = data.rep_count || 0;
            elements.angleValue.textContent = (data.knee_angle || 180) + '°';
            elements.feedback.textContent = data.feedback || 'Keep going!';

            // Update progress ring
            const progress = data.progress || 0;
            const circumference = 377;
            const offset = circumference - (progress / 100 * circumference);
            elements.progressRing.style.strokeDashoffset = offset;

            // Update phase indicator
            Object.values(elements.phases).forEach(p => p.classList.remove('active'));
            if (data.phase && elements.phases[data.phase]) {
                elements.phases[data.phase].classList.add('active');
            }

            // Update robot
            updateRobotMood(data.rep_count || 0, parseInt(elements.targetReps.textContent) || 10, false);
        } else {
            elements.bodyStatus.style.display = 'block';
            elements.bodyStatus.className = 'body-status not-detected';
            elements.bodyStatusText.textContent = '⚠ Move so camera can see you';
            elements.feedback.textContent = data.message || 'Position yourself in camera view';
        }
    } else if (data.type === 'started') {
        elements.targetReps.textContent = data.target_reps;
        elements.feedback.textContent = `Let's do ${data.target_reps} squats!`;
        resetRobotMood();
        setRobotState('watching');
    } else if (data.type === 'stopped') {
        elements.feedback.textContent = `Great workout! ${data.rep_count} reps!`;
        if (data.rep_count >= parseInt(elements.targetReps.textContent)) {
            setRobotState('celebrating');
        }
    }
}

function updateDuration() {
    if (!startTime) return;
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    elements.duration.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Robot state management
function setRobotState(state) {
    elements.robotStage.classList.remove('nodding', 'celebrating', 'watching', 'idle');
    if (state) {
        elements.robotStage.classList.add(state);
    }
}

function updateRobotMood(repCount, targetReps, isComplete) {
    // Nod on new rep
    if (repCount > lastRepCount) {
        lastRepCount = repCount;
        setRobotState('nodding');
        setTimeout(() => setRobotState('watching'), 400);
    }

    const progress = (repCount / targetReps) * 100;
    let emoji, text;

    if (isComplete || repCount >= targetReps) {
        emoji = '🎉';
        text = 'Amazing workout!';
        setRobotState('celebrating');
    } else if (progress >= 75) {
        emoji = '🔥';
        text = 'Almost there!';
    } else if (progress >= 50) {
        emoji = '💪';
        text = 'Halfway! Keep going!';
    } else if (progress >= 25) {
        emoji = '👍';
        text = 'Great form!';
    } else if (repCount > 0) {
        emoji = '😊';
        text = 'Nice start!';
    } else {
        emoji = '👀';
        text = 'Watching you...';
    }

    elements.moodEmoji.textContent = emoji;
    elements.moodText.textContent = text;
}

function resetRobotMood() {
    lastRepCount = 0;
    setRobotState('watching');
    elements.moodEmoji.textContent = '👀';
    elements.moodText.textContent = 'Watching you...';
}

// Audio playback
async function playAudioFromBase64(base64Data, format) {
    return new Promise((resolve, reject) => {
        try {
            const mimeType = format === 'mp3' ? 'audio/mpeg' : 'audio/wav';
            const binary = atob(base64Data);
            const bytes = new Uint8Array(binary.length);
            for (let i = 0; i < binary.length; i++) {
                bytes[i] = binary.charCodeAt(i);
            }
            const blob = new Blob([bytes], { type: mimeType });
            const url = URL.createObjectURL(blob);

            const audio = new Audio(url);
            audio.onended = () => {
                URL.revokeObjectURL(url);
                resolve();
            };
            audio.onerror = (e) => {
                URL.revokeObjectURL(url);
                reject(e);
            };
            audio.play().catch(reject);
        } catch (e) {
            reject(e);
        }
    });
}

async function processAudioQueue() {
    if (isPlayingAudio || audioQueue.length === 0) return;

    isPlayingAudio = true;
    const { data, format } = audioQueue.shift();

    try {
        await playAudioFromBase64(data, format);
    } catch (e) {
        console.error('Audio playback error:', e);
    }

    isPlayingAudio = false;
    processAudioQueue();
}

function queueAudio(data, format) {
    if (audioQueue.length < 3) {
        audioQueue.push({ data, format });
        processAudioQueue();
    }
}
