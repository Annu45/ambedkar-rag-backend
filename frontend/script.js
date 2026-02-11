import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const container = document.getElementById('canvas-container');

// 1. SCENE SETUP
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000); 

// 2. CAMERA FOCUS (Original Side Position)
const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
camera.position.set(0, 1.4, 3.8); 

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setPixelRatio(window.devicePixelRatio);
container.appendChild(renderer.domElement);

// 3. LIGHTING
scene.add(new THREE.AmbientLight(0xffffff, 1.5));
const dirLight = new THREE.DirectionalLight(0xffffff, 2.3);
dirLight.position.set(2, 2, 5);
scene.add(dirLight);

// 4. DRACO LOADER SETUP (Crucial for loading Dr_ambedkar2.glb)
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');

const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);

let mixer;

// 5. LOAD THE MODEL
loader.load('./models/Dr_ambedkar2.glb', (gltf) => {
    const avatar = gltf.scene;
    avatar.scale.set(1.15, 1.15, 1.15);
    avatar.position.set(0, -1, 0); 
    scene.add(avatar);

    if (gltf.animations.length > 0) {
        mixer = new THREE.AnimationMixer(avatar);
        mixer.clipAction(gltf.animations[0]).play();
    }
}, undefined, (error) => {
    console.error('Error loading avatar:', error);
});

// 6. CONTROLS (Center on Avatar)
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.enablePan = false;
controls.target.set(0, 1.2, 0); // Focuses on the face
controls.update();

// 7. RESPONSIVE SIZING
window.addEventListener('resize', () => {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
});

const clock = new THREE.Clock();
function animate() {
    requestAnimationFrame(animate);
    if (mixer) mixer.update(clock.getDelta());
    controls.update();
    renderer.render(scene, camera);
}
animate();

// 8. CHAT INTEGRATION
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
        
        // Browser Native Speech
        const utterance = new SpeechSynthesisUtterance(data.response);
        utterance.lang = "en-IN";
        window.speechSynthesis.speak(utterance);
    } catch (e) {
        status.innerText = "Connection failed.";
    }
};