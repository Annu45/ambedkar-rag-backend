import * as THREE from "https://unpkg.com/three@0.158.0/build/three.module.js";
import { GLTFLoader } from "https://unpkg.com/three@0.158.0/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "https://unpkg.com/three@0.158.0/examples/jsm/loaders/DRACOLoader.js";
import { OrbitControls } from "https://unpkg.com/three@0.158.0/examples/jsm/controls/OrbitControls.js";

let mixer;
let talkingAction;
const clock = new THREE.Clock();
const synth = window.speechSynthesis;

// 1. Audio Logic
function speakWithMaleVoice(text) {
  const cleanText = text.replace(/[.*#_~]/g, ''); 
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(cleanText);
  const voices = synth.getVoices();
  const maleVoice = voices.find(v => 
    v.name.includes("Google UK English Male") || 
    v.name.toLowerCase().includes("male")
  ) || voices[0];

  utterance.voice = maleVoice;
  utterance.pitch = 0.85; 
  utterance.rate = 0.95;  

  utterance.onstart = () => { if (talkingAction) talkingAction.reset().play(); };
  utterance.onend = () => { if (talkingAction) talkingAction.fadeOut(0.5); };
  synth.speak(utterance);
}

// 2. API Call Logic
window.askQuestion = async function () {
  const question = document.getElementById("question").value;
  if (!question) return;
  const answerDiv = document.getElementById("answer");
  answerDiv.innerText = "Thinking...";
  
  try {
    const response = await fetch("https://ambedkar-api.onrender.com/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
    });
    const data = await response.json();
    answerDiv.innerText = data.answer || "No answer returned";
    speakWithMaleVoice(answerDiv.innerText);
  } catch (err) {
    answerDiv.innerText = "Error connecting to Cloud API.";
  }
};

// 3. Three.js Scene Setup
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
const container = document.getElementById("avatar-container");
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// Lighting - Stronger for better visibility
scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 2));
const dirLight = new THREE.DirectionalLight(0xffffff, 2);
dirLight.position.set(5, 10, 7);
scene.add(dirLight);

// 4. Model Loading - FIXED PATH
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("https://www.gstatic.com/draco/v1/decoders/");
const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);

// FIXED: Removed "./models/" because file is in "frontend/models" 
// and script.js is likely in "frontend/"
loader.load("models/Dr_ambedkar2.glb", (gltf) => {
  const model = gltf.scene;
  model.scale.set(0.25, 0.25, 0.25);
  scene.add(model);

  // Auto-Center Camera on Model
  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  camera.position.set(0, size.y * 0.6, 3); // Positioned to see head/chest
  camera.lookAt(0, size.y * 0.5, 0);

  if (gltf.animations.length) {
    mixer = new THREE.AnimationMixer(model);
    const clip = gltf.animations.find(c => c.name.includes("Anim.001"));
    if (clip) talkingAction = mixer.clipAction(clip);
  }
}, undefined, (err) => console.error("Model Load Error:", err));

function animate() {
  requestAnimationFrame(animate);
  if (mixer) mixer.update(clock.getDelta());
  renderer.render(scene, camera);
}
animate();