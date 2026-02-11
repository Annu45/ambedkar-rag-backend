import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js'; // NEW IMPORT
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// 1. SCENE SETUP
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000); 

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 1.4, 3.5);

const container = document.getElementById('canvas-container');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(window.devicePixelRatio);
container.appendChild(renderer.domElement);

// 2. LIGHTING
scene.add(new THREE.AmbientLight(0xffffff, 1.5));
const dirLight = new THREE.DirectionalLight(0xffffff, 2);
dirLight.position.set(2, 2, 5);
scene.add(dirLight);

// 3. DRACO & GLTF LOADER SETUP (This fixes the error)
const dracoLoader = new DRACOLoader();
// Use Google's hosted decoder so you don't have to upload more files
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');

const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader); // Connect Draco to GLTF

let mixer;

// Loading the model with the confirmed filename
loader.load('./models/Dr_ambedkar2.glb', (gltf) => {
    const avatar = gltf.scene;
    avatar.scale.set(1.1, 1.1, 1.1);
    avatar.position.set(0, -1, 0);
    scene.add(avatar);

    if (gltf.animations.length > 0) {
        mixer = new THREE.AnimationMixer(avatar);
        mixer.clipAction(gltf.animations[0]).play();
    }
    console.log("✅ Avatar loaded with Draco support!");
}, undefined, (error) => {
    console.error('Error loading avatar:', error);
});

// 4. ANIMATION & CONTROLS
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.enablePan = false;

const clock = new THREE.Clock();
function animate() {
    requestAnimationFrame(animate);
    if (mixer) mixer.update(clock.getDelta());
    controls.update();
    renderer.render(scene, camera);
}
animate();

// 5. WINDOW RESIZE
window.addEventListener('resize', () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
});

// 6. CHAT LOGIC
window.sendMessage = async function() {
    const input = document.getElementById("user-input");
    const status = document.getElementById("status-text");
    if (!input.value) return;

    status.innerText = "Thinking...";
    const question = input.value;
    input.value = "";

    try {
        const res = await fetch("https://ambedkar-api.onrender.com/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: question })
        });
        const data = await res.json();
        status.innerText = "";
        speakText(data.response);
    } catch (e) {
        status.innerText = "Offline.";
    }
};

function speakText(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    window.speechSynthesis.speak(utterance);
}