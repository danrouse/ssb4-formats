function init() {
  var container, scene, renderer, camera, light, clock, loader;
  var WIDTH, HEIGHT, VIEW_ANGLE, ASPECT, NEAR, FAR;

  container = document.querySelector('body');

  clock = new THREE.Clock();

  WIDTH = window.innerWidth,
  HEIGHT = window.innerHeight;

  VIEW_ANGLE = 45,
  ASPECT = WIDTH / HEIGHT,
  NEAR = 1,
  FAR = 10000;

  scene = new THREE.Scene();

  renderer = new THREE.WebGLRenderer({antialias: true});

  renderer.setSize(WIDTH, HEIGHT);
  renderer.shadowMap.Enabled = true;
  renderer.shadowMapSoft = true;
  renderer.shadowMap.Type = THREE.PCFShadowMap;
  renderer.shadowMapAutoUpdate = true;

  container.appendChild(renderer.domElement);

  camera = new THREE.PerspectiveCamera(VIEW_ANGLE, ASPECT, NEAR, FAR);

  camera.position.set(0, 20, 50);
  camera.rotation.x = -Math.PI / 12;

  scene.add(camera);

  light = new THREE.DirectionalLight(0xffffff);

  light.position.set(0, 50, 100);
  light.castShadow = true;
  light.shadowCameraLeft = -60;
  light.shadowCameraTop = -60;
  light.shadowCameraRight = 60;
  light.shadowCameraBottom = 60;
  light.shadowCameraNear = 1;
  light.shadowCameraFar = 1000;
  light.shadowBias = -.0001
  light.shadowMapWidth = light.shadowMapHeight = 1024;
  light.shadowDarkness = .7;

  scene.add(light);

  var controls = new THREE.OrbitControls(camera, document, renderer.domElement);

  loader = new THREE.JSONLoader();
  var mesh, helper, mixer;
  loader.load('model.json', function (geometry, materials) {
    var material = new THREE.MeshLambertMaterial({});
    material.skinning = true;

    mesh = new THREE.SkinnedMesh(
     geometry,
     material
    );
    mesh.receiveShadow = true;
    mesh.castShadow = true;
    mesh.rotation.y = -Math.PI/5;

    window.mesh = mesh;
    window.bone = function(name) {
      for(var i in mesh.skeleton.bones) {
        if(mesh.skeleton.bones[i].name.toLowerCase() === name.toLowerCase()) {
          return mesh.skeleton.bones[i];
        }
      }
    }

    helper = new THREE.SkeletonHelper(mesh);
    helper.material.linewidth = 3;
    scene.add(helper);

    mixer = new THREE.AnimationMixer(mesh);
    var animations = {};

    function play(name) {
      var anim = new THREE.AnimationAction(animations[name]);
      console.log('Playing animation', anim);
      mixer.removeAllActions();
      mixer.play(anim);
    }

    for(var i in geometry.animations) {
      var animName = geometry.animations[i].name;
      animations[animName] = geometry.animations[i];

      var elem = document.createElement('button');
      elem.innerText = animName;
      elem.addEventListener('click', play.bind(null, animName));
      buttons.appendChild(elem);
    }

    //console.log(geometry.animations[0]);
    scene.add(mesh);
    render(); 
  });

  var lastFrameTime = 0;
  function render(time) {
    var dt = time - lastFrameTime;

    // mesh.rotation.y += .01;
    controls.update();

    renderer.render(scene, camera);
    requestAnimationFrame(render);
    if(mixer) {
      //console.log('update', dt);
      mixer.update(clock.getDelta() / 2);
      helper.update();
    }

    lastFrameTime = time;
  }
}

document.addEventListener('DOMContentLoaded', init);
