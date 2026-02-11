import * as THREE from "https://unpkg.com/three@0.158.0/build/three.module.js";
import { GLTFLoader } from "https://unpkg.com/three@0.158.0/examples/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "https://unpkg.com/three@0.158.0/examples/jsm/loaders/DRACOLoader.js";
import { OrbitControls } from "https://unpkg.com/three@0.158.0/examples/jsm/controls/OrbitControls.js";

let mixer, talkingAction, model;
const clock = new THREE.Clock();
const synth = window.speechSynthesis;

// 1. SCENE SETUP
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x000000);
const container = document.getElementById("avatar-container");
const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// 2. LIGHTING
scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.5));
const dirLight = new THREE.DirectionalLight(0xffffff, 2);
dirLight.position.set(5, 10, 7);
scene.add(dirLight);

// 3. CONTROLS (LOCKED TO PREVENT MOVING)
const controls = new OrbitControls(camera, renderer.domElement);
controls.enablePan = false;
controls.enableZoom = false;
controls.enableRotate = false;

// 4. LOAD AVATAR
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("https://www.gstatic.com/draco/v1/decoders/");
const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);

loader.load("models/Dr_ambedkar2.glb", (gltf) => {
  model = gltf.scene;
  model.scale.set(0.25, 0.25, 0.25); // ORIGINAL SCALE
  model.rotation.y = Math.PI / 2; // ORIGINAL ROTATION

  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());

  // Center model in its local space
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

// 5. ANIMATION LOOP
function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  if (mixer) mixer.update(delta);
  renderer.render(scene, camera);
}
animate();

// 6. CHAT FUNCTION
window.askQuestion = async function () {
  const questionInput = document.getElementById("question");
  const answerDiv = document.getElementById("answer");
  if (!questionInput.value) return;

  answerDiv.innerText = "Thinking...";
  try {
    const response = await fetch("https://ambedkar-api.onrender.com/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: questionInput.value })
    });
    const data = await response.json();
    answerDiv.innerText = data.response;
    
    // Voice
    const utterance = new SpeechSynthesisUtterance(data.response);
    utterance.lang = "en-IN";
    utterance.onstart = () => { if (talkingAction) talkingAction.reset().play(); };
    utterance.onend = () => { if (talkingAction) talkingAction.fadeOut(0.5); };
    synth.speak(utterance);
    
    questionInput.value = "";
  } catch (err) {
    answerDiv.innerText = "Connection failed.";
  }
};