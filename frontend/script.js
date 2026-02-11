import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// 1. SETUP SCENE
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000); // Pure Black

// 2. SETUP CAMERA
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 1.4, 3); // Positioned to see the face

// 3. SETUP RENDERER (The part that was broken)
const container = document.getElementById('canvas-container'); // MUST MATCH HTML ID

if (!container) {
    console.error("CRITICAL ERROR: 'canvas-container' not found in HTML!");
}

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
// Add the canvas to the HTML
container.appendChild(renderer.domElement);

// 4. LIGHTING (Critical for visibility)
const ambientLight = new THREE.AmbientLight(0xffffff, 1.5); // Soft white light
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 2);
dirLight.position.set(2, 2, 5);
scene.add(dirLight);

// 5. LOAD THE AVATAR
const loader = new GLTFLoader();
let avatar;
let mixer; // For animations

loader.load(
    './models/avatar.glb', // Path to your model
    (gltf) => {
        avatar = gltf.scene;
        
        // Scale and Position
        avatar.scale.set(1.1, 1.1, 1.1);
        avatar.position.set(0, -1, 0); // Move down slightly
        
        scene.add(avatar);
        console.log("✅ Avatar Loaded Successfully!");

        // Setup Animation (Idle)
        mixer = new THREE.AnimationMixer(avatar);
        if (gltf.animations.length > 0) {
            const action = mixer.clipAction(gltf.animations[0]);
            action.play();
        }
    },
    (xhr) => {
        console.log(`Loading: ${(xhr.loaded / xhr.total * 100)}%`);
    },
    (error) => {
        console.error('⚠️ Error loading avatar:', error);
    }
);

// 6. CONTROLS (Allow rotating)
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.enablePan = false;
controls.minDistance = 2;
controls.maxDistance = 5;

// 7. RESPONSIVE WINDOW
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// 8. ANIMATION LOOP
const clock = new THREE.Clock();
function animate() {
    requestAnimationFrame(animate);
    
    const delta = clock.getDelta();
    if (mixer) mixer.update(delta);
    
    controls.update();
    renderer.render(scene, camera);
}
animate();

// 9. CONNECT CHAT TO BACKEND
window.sendMessage = async function() {
    const inputField = document.getElementById("user-input");
    const statusText = document.getElementById("status-text");
    const question = inputField.value;

    if (!question) return;

    statusText.innerText = "Thinking...";
    inputField.value = "";

    try {
        // Send to Render Backend
        const response = await fetch("https://ambedkar-api.onrender.com/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: question })
        });

        const data = await response.json();
        statusText.innerText = ""; // Clear status
        
        // Speak the Answer
        speakText(data.response);

    } catch (error) {
        statusText.innerText = "Error connecting to AI.";
        console.error(error);
    }
};

// 10. TEXT TO SPEECH (Browser Native)
function speakText(text) {
    const synth = window.speechSynthesis;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN"; // Indian English
    utterance.rate = 0.9;
    synth.speak(utterance);
}