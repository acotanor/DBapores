document.addEventListener("DOMContentLoaded", () => {
  const menuCluster = document.getElementById("menuCluster");
  const logoOrb = document.getElementById("logoOrb");
  const option1 = document.getElementById("opt1");
  const option2 = document.getElementById("opt2");
  const option3 = document.getElementById("opt3");
  const bubbleParticles = document.getElementById("bubbleParticles");

  const magnetShells = Array.from(document.querySelectorAll(".mini-orb-shell"));

  const MAGNET_RANGE = 190;
  const MAGNET_STRENGTH = 12;

  const PARTICLE_COUNT = 18;
  const PARTICLE_MIN_SIZE = 10;
  const PARTICLE_MAX_SIZE = 26;
  const PARTICLE_BURST_MIN = 28;
  const PARTICLE_BURST_MAX = 82;
  const PARTICLE_SIDE_DRIFT = 60;
  const PARTICLE_DURATION_MIN = 3600;
  const PARTICLE_DURATION_MAX = 5600;
  const PARTICLE_STAGGER_MAX = 180;

  let isNavigating = false;

  function setMenuState(isOpen) {
    menuCluster.classList.toggle("open", isOpen);
    logoOrb.setAttribute("aria-expanded", String(isOpen));

    if (!isOpen) {
      resetMagnetEffect();
    }
  }

  function animateLogoBubble() {
    logoOrb.animate(
      [
        { transform: "translate(-50%, -50%) scale(1)" },
        { transform: "translate(-50%, -50%) scale(0.94)" },
        { transform: "translate(-50%, -50%) scale(1.02)" },
        { transform: "translate(-50%, -50%) scale(1)" }
      ],
      {
        duration: 260,
        easing: "ease-out"
      }
    );
  }

  function randomBetween(min, max) {
    return Math.random() * (max - min) + min;
  }

  function emitBubbleParticles(count = PARTICLE_COUNT) {
    if (!bubbleParticles || !logoOrb) return;

    const logoRect = logoOrb.getBoundingClientRect();
    const centerX = logoRect.left + logoRect.width / 2;
    const centerY = logoRect.top + logoRect.height / 2;

    for (let i = 0; i < count; i += 1) {
      const particle = document.createElement("span");
      particle.className = "bubble-particle";

      const size = randomBetween(PARTICLE_MIN_SIZE, PARTICLE_MAX_SIZE);

      const spawnAngle = randomBetween(-Math.PI * 0.95, -Math.PI * 0.05);
      const spawnRadius = randomBetween(8, logoRect.width * 0.22);

      const startOffsetX = Math.cos(spawnAngle) * spawnRadius;
      const startOffsetY = Math.sin(spawnAngle) * spawnRadius;

      const burstAngle = randomBetween(0, Math.PI * 2);
      const burstDistance = randomBetween(PARTICLE_BURST_MIN, PARTICLE_BURST_MAX);
      const burstX = startOffsetX + Math.cos(burstAngle) * burstDistance;
      const burstY = startOffsetY + Math.sin(burstAngle) * burstDistance;

      const topExitY = -(centerY + size + randomBetween(30, 100));
      const finalX = burstX + randomBetween(-PARTICLE_SIDE_DRIFT, PARTICLE_SIDE_DRIFT);

      const midX = burstX + randomBetween(-14, 14);
      const midY = burstY + randomBetween(-8, 12);

      const duration = randomBetween(PARTICLE_DURATION_MIN, PARTICLE_DURATION_MAX);
      const delay = randomBetween(0, PARTICLE_STAGGER_MAX);
      const rotation = randomBetween(-18, 18);

      particle.style.width = `${size.toFixed(2)}px`;
      particle.style.height = `${size.toFixed(2)}px`;
      particle.style.left = `${centerX.toFixed(2)}px`;
      particle.style.top = `${centerY.toFixed(2)}px`;

      bubbleParticles.appendChild(particle);

      const animation = particle.animate(
        [
          {
            transform: `translate(-50%, -50%) translate(${startOffsetX.toFixed(2)}px, ${startOffsetY.toFixed(2)}px) scale(0.2) rotate(0deg)`,
            opacity: 0,
            offset: 0
          },
          {
            transform: `translate(-50%, -50%) translate(${(burstX * 0.55).toFixed(2)}px, ${(burstY * 0.55).toFixed(2)}px) scale(0.85) rotate(${(rotation * 0.25).toFixed(2)}deg)`,
            opacity: 0.95,
            offset: 0.12
          },
          {
            transform: `translate(-50%, -50%) translate(${midX.toFixed(2)}px, ${midY.toFixed(2)}px) scale(1) rotate(${(rotation * 0.4).toFixed(2)}deg)`,
            opacity: 0.98,
            offset: 0.22
          },
          {
            transform: `translate(-50%, -50%) translate(${(finalX * 0.45).toFixed(2)}px, ${(topExitY * 0.35).toFixed(2)}px) scale(1.04) rotate(${(rotation * 0.65).toFixed(2)}deg)`,
            opacity: 0.96,
            offset: 0.55
          },
          {
            transform: `translate(-50%, -50%) translate(${(finalX * 0.82).toFixed(2)}px, ${(topExitY * 0.82).toFixed(2)}px) scale(1.08) rotate(${(rotation * 0.9).toFixed(2)}deg)`,
            opacity: 0.93,
            offset: 0.88
          },
          {
            transform: `translate(-50%, -50%) translate(${finalX.toFixed(2)}px, ${topExitY.toFixed(2)}px) scale(1.1) rotate(${rotation.toFixed(2)}deg)`,
            opacity: 0,
            offset: 1
          }
        ],
        {
          duration,
          delay,
          easing: "cubic-bezier(.22, .72, .2, 1)",
          fill: "forwards"
        }
      );

      animation.finished
        .catch(() => {})
        .finally(() => {
          particle.remove();
        });
    }
  }

  function animateBubblesExitAndGoTo(url) {
    if (isNavigating) return;
    isNavigating = true;

    menuCluster.classList.add("transitioning");
    document.body.classList.add("is-transitioning");

    resetMagnetEffect();
    emitBubbleParticles(26);

    const targets = [logoOrb, option1, option2, option3];
    let longestEnd = 0;

    targets.forEach((element, index) => {
      if (!element) return;

      const startTransform = getComputedStyle(element).transform;
      const safeStartTransform =
        startTransform && startTransform !== "none"
          ? startTransform
          : "translate(-50%, -50%)";

      const driftX = randomBetween(-90, 90);
      const driftY = -(window.innerHeight + randomBetween(140, 260));
      const rotation = randomBetween(-18, 18);
      const scale = randomBetween(0.88, 1.03);
      const duration = randomBetween(1650, 2550);
      const delay = randomBetween(index * 70, index * 70 + 240);

      const endAt = duration + delay;
      if (endAt > longestEnd) longestEnd = endAt;

      element.animate(
        [
          {
            transform: safeStartTransform,
            opacity: 1,
            filter: "blur(0px)"
          },
          {
            offset: 0.22,
            transform: `${safeStartTransform} translate(${(driftX * 0.28).toFixed(2)}px, ${(-window.innerHeight * 0.18).toFixed(2)}px) rotate(${(rotation * 0.25).toFixed(2)}deg) scale(1.01)`,
            opacity: 1,
            filter: "blur(0px)"
          },
          {
            offset: 0.65,
            transform: `${safeStartTransform} translate(${(driftX * 0.72).toFixed(2)}px, ${(driftY * 0.62).toFixed(2)}px) rotate(${(rotation * 0.68).toFixed(2)}deg) scale(${(scale + 0.03).toFixed(3)})`,
            opacity: 0.86,
            filter: "blur(0.6px)"
          },
          {
            transform: `${safeStartTransform} translate(${driftX.toFixed(2)}px, ${driftY.toFixed(2)}px) rotate(${rotation.toFixed(2)}deg) scale(${scale.toFixed(3)})`,
            opacity: 0,
            filter: "blur(2.4px)"
          }
        ],
        {
          duration,
          delay,
          easing: "cubic-bezier(.22, .61, .25, 1)",
          fill: "forwards"
        }
      );
    });

    window.setTimeout(() => {
      window.location.href = url;
    }, longestEnd + 80);
  }

  function toggleMenu(event) {
    if (isNavigating) return;

    event.preventDefault();
    event.stopPropagation();

    animateLogoBubble();
    emitBubbleParticles();

    const isOpen = menuCluster.classList.contains("open");
    setMenuState(!isOpen);
  }

  function handleOptionClick(event, message) {
    if (isNavigating) return;
    event.preventDefault();
    alert(message);
  }

  function closeMenuOnOutsideClick(event) {
    if (isNavigating) return;

    if (!menuCluster.contains(event.target) && menuCluster.classList.contains("open")) {
      setMenuState(false);
    }
  }

  function handleLogoKeydown(event) {
    if (isNavigating) return;

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleMenu(event);
    }
  }

  function resetMagnetEffect() {
    magnetShells.forEach((shell) => {
      const orb = shell.querySelector(".mini-orb");
      if (!orb) return;

      orb.style.setProperty("--magnet-x", "0px");
      orb.style.setProperty("--magnet-y", "0px");
    });
  }

  function updateMagnetEffect(cursorX, cursorY) {
    if (!menuCluster.classList.contains("open") || isNavigating) {
      return;
    }

    magnetShells.forEach((shell) => {
      const orb = shell.querySelector(".mini-orb");
      if (!orb) return;

      const rect = shell.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const deltaX = cursorX - centerX;
      const deltaY = cursorY - centerY;
      const distance = Math.hypot(deltaX, deltaY);

      if (distance >= MAGNET_RANGE) {
        orb.style.setProperty("--magnet-x", "0px");
        orb.style.setProperty("--magnet-y", "0px");
        return;
      }

      const proximity = 1 - distance / MAGNET_RANGE;
      const easedProximity = proximity * proximity;
      const safeDistance = Math.max(distance, 0.001);

      const offsetX = (deltaX / safeDistance) * MAGNET_STRENGTH * easedProximity;
      const offsetY = (deltaY / safeDistance) * MAGNET_STRENGTH * easedProximity;

      orb.style.setProperty("--magnet-x", `${offsetX.toFixed(2)}px`);
      orb.style.setProperty("--magnet-y", `${offsetY.toFixed(2)}px`);
    });
  }

  logoOrb.addEventListener("click", toggleMenu);
  logoOrb.addEventListener("keydown", handleLogoKeydown);

  option1.addEventListener("click", (event) => {
    event.preventDefault();
    animateBubblesExitAndGoTo("opcion1.html");
  });

  option2.addEventListener("click", (event) => {
    handleOptionClick(event, "Opción 2");
  });

  option3.addEventListener("click", (event) => {
    handleOptionClick(event, "Opción 3");
  });

  document.addEventListener("mousemove", (event) => {
    updateMagnetEffect(event.clientX, event.clientY);
  });

  document.addEventListener("mouseleave", () => {
    resetMagnetEffect();
  });

  document.addEventListener("click", closeMenuOnOutsideClick);
});