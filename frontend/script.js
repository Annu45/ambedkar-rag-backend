import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// --- VISUAL LOGGING (Since you can't inspect) ---
const logBox = document.createElement('div');
logBox.style.position = 'absolute';
logBox.style.top = '10px';
logBox.style.left = '10px';
logBox.style.color = '#00ff00';
logBox.style.fontFamily = 'monospace';
logBox.style.zIndex = '9999';
logBox.style.background = 'rgba(0,0,0,0.8)';
logBox.style.padding = '10px';
logBox.style.pointerEvents = 'none'; // Let clicks pass through
document.body.appendChild(logBox);

function log(msg) {
    logBox.innerHTML += `> ${msg}<br>`;
    console.log(msg);
}

log("🚀 Starting 3D Engine...");

// 1. SETUP
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111111); // Dark Grey (Not Black, to see outlines)

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 1, 3); // Look from slightly above

const container = document.getElementById('canvas-container');
if (!container) {
    log("❌ ERROR: 'canvas-container' div missing!");
} else {
    log("✅ Container found.");
}

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
container.appendChild(renderer.domElement);

// 2. LIGHTS
const ambient = new THREE.AmbientLight(0xffffff, 1);
scene.add(ambient);
const dirLight = new THREE.DirectionalLight(0xffffff, 2);
dirLight.position.set(2, 2, 5);
scene.add(dirLight);

// 3. DEBUG CUBE (The Red Box)
const geometry = new THREE.BoxGeometry(0.5, 0.5, 0.5);
const material = new THREE.MeshStandardMaterial({ color: 0xff0000 });
const cube = new THREE.Mesh(geometry, material);
cube.position.set(0, 0, 0); // Center
scene.add(cube);
log("✅ Red Debug Cube added.");

// 4. LOAD AVATAR
const loader = new GLTFLoader();
log("⏳ Loading Avatar...");
loader.load(
    './models/avatar.glb', // Try standard path
    (gltf) => {
        const avatar = gltf.scene;
        avatar.position.set(0, -1, 0);
        avatar.scale.set(1.1, 1.1, 1.1);
        scene.add(avatar);
        log("🎉 Avatar Loaded Successfully!");
        
        // Hide Cube if Avatar loads
        cube.visible = false; 
    },
    (xhr) => {
        // Progress
    },
    (error) => {
        log("⚠️ Avatar Load Failed!");
        log("Trying backup path...");
        // Backup: Try loading from root if frontend/ fails
        loader.load('models/avatar.glb', (gltf) => {
             const avatar = gltf.scene;
             avatar.position.set(0, -1, 0);
             avatar.scale.set(1.1, 1.1, 1.1);
             scene.add(avatar);
             log("🎉 Backup Path Worked!");
             cube.visible = false;
        }, undefined, (err2) => {
            log("❌ MODEL ERROR: Could not find avatar.glb");
            log("Check 'models' folder in GitHub.");
        });
    }
);

// 5. ANIMATE
function animate() {
    requestAnimationFrame(animate);
    cube.rotation.x += 0.01; // Spin the cube
    cube.rotation.y += 0.01;
    renderer.render(scene, camera);
}
animate();

// 6. RESIZE HANDLER
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});