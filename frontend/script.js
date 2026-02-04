console.log("SCRIPT MODULE LOADED");

import * as THREE from "https://unpkg.com/three@0.158.0/build/three.module.js";
import { GLTFLoader } from "https://unpkg.com/three@0.158.0/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "https://unpkg.com/three@0.158.0/examples/jsm/loaders/DRACOLoader.js";
import { OrbitControls } from "https://unpkg.com/three@0.158.0/examples/jsm/controls/OrbitControls.js";

let mixer;
let talkingAction;
const clock = new THREE.Clock();
const synth = window.speechSynthesis;

/* ========================== SPEECH SYNTHESIS HELPER ========================== */
function speakWithMaleVoice(text) {
  // Cancel any ongoing speech
  synth.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  const voices = synth.getVoices();

  // 1. Try to find a high-quality Indian Male or International Male voice
  const maleVoice = voices.find(v => 
    v.name.includes("Google UK English Male") || 
    v.name.includes("Rishi") || 
    (v.name.includes("Male") && v.lang.startsWith("en"))
  ) || voices[0]; // Fallback to first voice if no specific male voice found

  utterance.voice = maleVoice;
  utterance.pitch = 0.85; // Lower pitch for a more authoritative male tone
  utterance.rate = 0.95;  // Slightly slower pace for clarity

  // 2. Sync with Avatar Animation
  utterance.onstart = () => {
    if (talkingAction) {
      talkingAction.reset().play();
    }
  };

  utterance.onend = () => {
    if (talkingAction) {
      talkingAction.fadeOut(0.5); // Smoothly stop talking
    }
  };

  synth.speak(utterance);
}

// Load voices (required for Chrome/Edge async loading)
if (synth.onvoiceschanged !== undefined) {
  synth.onvoiceschanged = () => synth.getVoices();
}

/* ========================== RAG QUESTION FUNCTION ========================== */
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
    const answer = data.answer || "No answer returned";
    answerDiv.innerText = answer;
    
    // Trigger the Male Voice instead of playing an audio file
    speakWithMaleVoice(answer);

  } catch (err) {
    console.error(err);
    answerDiv.innerText = "Error connecting to the Cloud API. Please try again.";
  }
};

/* ========================== SCENE + CAMERA ========================== */
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);

/* ========================== RENDERER ========================== */
const container = document.getElementById("avatar-container");
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setClearColor(0x000000, 1);
container.appendChild(renderer.domElement);

/* ========================== LIGHTS ========================== */
scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.5));
const dirLight = new THREE.DirectionalLight(0xffffff, 2);
dirLight.position.set(5, 10, 7);
scene.add(dirLight);

/* ========================== CONTROLS (LOCKED) ========================== */
const controls = new OrbitControls(camera, renderer.domElement);
controls.enablePan = false; controls.enableZoom = false; controls.enableRotate = false;

/* ========================== LOAD MODEL ========================== */
let model;
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("https://www.gstatic.com/draco/v1/decoders/");
const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);

loader.load("./models/Dr_ambedkar2.glb", (gltf) => {
  model = gltf.scene;
  model.scale.set(0.25, 0.25, 0.25);
  model.rotation.y = Math.PI / 2;

  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());

  model.position.x -= center.x;
  model.position.z -= center.z;
  model.position.y -= box.min.y;

  scene.add(model);

  if (gltf.animations.length) {
    mixer = new THREE.AnimationMixer(model);
    const talkingClip = gltf.animations.find(c => c.name.includes("Anim.001"));
    if (talkingClip) {
      talkingAction = mixer.clipAction(talkingClip);
      talkingAction.loop = THREE.LoopRepeat;
    }
  }

  const fov = camera.fov * (Math.PI / 180);
  const distance = size.y / (2 * Math.tan(fov / 2));
  camera.position.set(0, size.y * 0.55, distance * 1.35);
  camera.lookAt(0, size.y * 0.55, 0);

}, undefined, (err) => console.error("GLB ERROR", err));

/* ========================== LOOP ========================== */
function animate() {
  requestAnimationFrame(animate);
  if (mixer) mixer.update(clock.getDelta());
  renderer.render(scene, camera);
}
animate();

/* ========================== RESIZE ========================== */
window.addEventListener("resize", () => {
  const w = container.clientWidth;
  const h = container.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
});