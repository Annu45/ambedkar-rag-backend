console.log("SCRIPT MODULE LOADED - RESTORED POSITION");

import * as THREE from "https://unpkg.com/three@0.158.0/build/three.module.js";
import { GLTFLoader } from "https://unpkg.com/three@0.158.0/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "https://unpkg.com/three@0.158.0/examples/jsm/loaders/DRACOLoader.js";
import { OrbitControls } from "https://unpkg.com/three@0.158.0/examples/jsm/controls/OrbitControls.js";

let mixer;
let talkingAction;
const clock = new THREE.Clock();
const synth = window.speechSynthesis;

function speakWithMaleVoice(text) {
  const cleanText = text.replace(/[.*#_~]/g, ''); 
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(cleanText);
  const voices = synth.getVoices();
  const maleVoice = voices.find(v => v.name.includes("Google UK English Male") || v.name.toLowerCase().includes("male")) || voices[0];
  utterance.voice = maleVoice;
  utterance.pitch = 0.85; 
  utterance.rate = 0.95;  

  utterance.onstart = () => { if (talkingAction) { talkingAction.reset().play(); } };
  utterance.onend = () => { if (talkingAction) { talkingAction.fadeOut(0.5); } };
  synth.speak(utterance);
}

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
    speakWithMaleVoice(answer);
  } catch (err) {
    console.error(err);
    answerDiv.innerText = "Backend error";
  }
};

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);

const container = document.getElementById("avatar-container");
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(container.clientWidth, container.clientHeight);
renderer.setClearColor(0x000000, 1);
container.appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.5));
const dirLight = new THREE.DirectionalLight(0xffffff, 2);
dirLight.position.set(5, 10, 7);
scene.add(dirLight);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enablePan = false;
controls.enableZoom = false;
controls.enableRotate = false;

let model;
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("https://www.gstatic.com/draco/v1/decoders/");
const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);

// FIXED PATH for your GitHub Structure
loader.load("models/Dr_ambedkar2.glb", (gltf) => {
  model = gltf.scene;
  model.scale.set(0.25, 0.25, 0.25); // ORIGINAL SCALE
  model.rotation.y = Math.PI / 2; // ORIGINAL ROTATION

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

  // ORIGINAL CAMERA FRAMING LOGIC
  const fov = camera.fov * (Math.PI / 180);
  const distance = size.y / (2 * Math.tan(fov / 2));
  camera.position.set(0, size.y * 0.55, distance * 1.35);
  camera.lookAt(0, size.y * 0.55, 0);

}, undefined, (err) => console.error("GLB ERROR", err));

function animate() {
  requestAnimationFrame(animate);
  if (mixer) mixer.update(clock.getDelta());
  renderer.render(scene, camera);
}
animate();

window.addEventListener("resize", () => {
  const w = container.clientWidth;
  const h = container.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
});